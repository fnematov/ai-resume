from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models import Organization, OrgStatus
from app.services.telegram.handler import handle_update
from app.workers.tasks import evaluate_submission, score_application

router = APIRouter()


@router.post("/webhook/{org_id}", status_code=status.HTTP_200_OK)
async def telegram_webhook(
    org_id: int,
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Per-org Telegram webhook. Verifies the secret-token header, then dispatches the update."""
    org = await db.get(Organization, org_id)
    if org is None or not org.telegram_configured or org.status != OrgStatus.active:
        # Always 200 so Telegram doesn't retry against a misconfigured org.
        return {"ok": True}
    if (
        not org.telegram_webhook_secret
        or x_telegram_bot_api_secret_token != org.telegram_webhook_secret
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bad secret token")

    update = await request.json()
    try:
        await handle_update(
            update,
            org,
            db,
            lambda app_id: score_application.delay(app_id),
            lambda sub_id: evaluate_submission.delay(sub_id),
        )
    except Exception:
        # Never surface 500 to Telegram; it would retry indefinitely.
        return {"ok": True}
    return {"ok": True}
