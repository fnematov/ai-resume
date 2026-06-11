from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_org
from app.core.security import decrypt_secret, encrypt_secret
from app.core.utils import random_token
from app.models import (
    ActivityActor,
    ActivityType,
    Application,
    ApplicationStage,
    Interview,
    InterviewProvider,
    InterviewStatus,
    Organization,
)
from app.schemas.scheduling import CalendlyConnectIn, CalendlyTokenIn, EventTypeOut
from app.services.activities import log_activity
from app.services.messaging import send_to_candidate
from app.services.scheduling import CalendlyClient, CalendlyError, verify_signature

router = APIRouter()


def _webhook_url(org_id: int) -> str:
    base = settings.public_base_url.rstrip("/")
    return f"{base}{settings.api_v1_prefix}/scheduling/calendly/webhook/{org_id}"


@router.post("/calendly/event-types", response_model=list[EventTypeOut])
async def calendly_event_types(
    payload: CalendlyTokenIn, _: Organization = Depends(get_current_org)
):
    """Validate a Calendly token and list the user's active event types (for selection)."""
    client = CalendlyClient(payload.token)
    try:
        me = await client.me()
        types = await client.event_types(me["uri"])
    except CalendlyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return [
        EventTypeOut(
            uri=t["uri"],
            name=t.get("name", "Event"),
            scheduling_url=t.get("scheduling_url", ""),
            duration=t.get("duration"),
        )
        for t in types
    ]


@router.post("/calendly/connect")
async def calendly_connect(
    payload: CalendlyConnectIn,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    client = CalendlyClient(payload.token)
    try:
        me = await client.me()
        org_uri = me.get("current_organization")
        if not org.calendly_webhook_signing_key:
            org.calendly_webhook_signing_key = random_token(24)
        try:
            await client.create_webhook(
                _webhook_url(org.id), org_uri, org.calendly_webhook_signing_key
            )
        except CalendlyError:
            # Webhook may already exist; booking still works via polling/manual. Don't hard-fail.
            pass
    except CalendlyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    org.calendly_token_enc = encrypt_secret(payload.token)
    org.calendly_event_type_uri = payload.event_type_uri
    org.calendly_scheduling_url = payload.scheduling_url
    await db.commit()
    return {"ok": True, "scheduling_url": payload.scheduling_url}


def _parse_invitee(payload: dict) -> dict:
    ev = payload.get("scheduled_event", {}) or {}
    loc = ev.get("location", {}) or {}
    join_url = loc.get("join_url")
    location = loc.get("location") if not join_url else None
    return {
        "start": ev.get("start_time"),
        "end": ev.get("end_time"),
        "join_url": join_url,
        "location": location,
        "utm_content": (payload.get("tracking", {}) or {}).get("utm_content", ""),
        "external_id": payload.get("uri"),
    }


@router.post("/calendly/webhook/{org_id}", status_code=status.HTTP_200_OK)
async def calendly_webhook(
    org_id: int,
    request: Request,
    calendly_webhook_signature: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    org = await db.get(Organization, org_id)
    if org is None:
        return {"ok": True}
    raw = await request.body()
    if not verify_signature(org.calendly_webhook_signing_key or "", calendly_webhook_signature, raw):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bad signature")

    body = await request.json()
    event = body.get("event")
    info = _parse_invitee(body.get("payload", {}) or {})

    # Map booking back to the application via utm_content=app_<id>.
    utm = info["utm_content"] or ""
    if not utm.startswith("app_"):
        return {"ok": True}
    try:
        application_id = int(utm.split("_", 1)[1])
    except (ValueError, IndexError):
        return {"ok": True}

    app_row = await db.get(Application, application_id)
    if app_row is None or app_row.org_id != org_id:
        return {"ok": True}

    def _dt(v):
        return datetime.fromisoformat(v.replace("Z", "+00:00")) if v else None

    if event == "invitee.created":
        interview = Interview(
            org_id=org_id,
            application_id=application_id,
            provider=InterviewProvider.calendly,
            scheduled_at=_dt(info["start"]),
            end_at=_dt(info["end"]),
            join_url=info["join_url"],
            location=info["location"],
            status=InterviewStatus.scheduled,
            external_id=info["external_id"],
            raw=body,
        )
        db.add(interview)
        app_row.stage = ApplicationStage.interview
        where = info["join_url"] or info["location"] or "the agreed location"
        await log_activity(
            db, application=app_row, type=ActivityType.interview_scheduled,
            actor=ActivityActor.candidate,
            summary=f"Interview booked for {info['start']}",
        )
        await send_to_candidate(
            db, app_row,
            f"✅ Your interview is confirmed for {info['start']}.\nJoin / location: {where}",
            actor=ActivityActor.system,
            activity_summary="Interview confirmation sent",
        )
        await db.commit()
    elif event == "invitee.canceled":
        existing = (
            await db.execute(
                select(Interview).where(
                    Interview.application_id == application_id,
                    Interview.external_id == info["external_id"],
                )
            )
        ).scalar_one_or_none()
        if existing:
            existing.status = InterviewStatus.canceled
            await log_activity(
                db, application=app_row, type=ActivityType.interview_canceled,
                actor=ActivityActor.candidate, summary="Interview canceled",
            )
            await db.commit()

    return {"ok": True}
