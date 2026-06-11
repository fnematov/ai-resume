from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_org_user
from app.models import (
    Activity,
    ActivityActor,
    ActivityType,
    Application,
    ApplicationSource,
    ApplicationStage,
    ApplicationStatus,
    Candidate,
    Interview,
    Message,
    MessageTemplate,
    Organization,
    Submission,
    TemplateType,
    User,
    Vacancy,
)
from app.schemas.application import (
    ActivityOut,
    ApplicationDetail,
    ApplicationListItem,
    StageUpdate,
    SubmissionOut,
)
from app.schemas.messaging import ActionIn, MessageOut, SendMessageIn
from app.schemas.scheduling import InterviewOut
from app.services.activities import log_activity
from app.services.extraction import ALLOWED_EXTENSIONS, guess_mime
from app.services.messaging import build_context, render, send_to_candidate
from app.services.offer import generate_offer_pdf
from app.services.storage import read_resume, resume_exists, save_resume
from app.services.telegram.state import set_awaiting_submission
from app.workers.tasks import score_application

router = APIRouter()

# action -> (target stage, activity type, default template type)
_ACTIONS: dict[str, tuple] = {
    "test_task": (ApplicationStage.test_task, ActivityType.message_sent, TemplateType.test_task),
    "interview": (ApplicationStage.interview, ActivityType.message_sent, TemplateType.interview),
    "offer": (ApplicationStage.offer, ActivityType.offer_sent, TemplateType.offer),
    "reject": (ApplicationStage.rejected, ActivityType.rejected, TemplateType.rejection),
}


async def _get_owned(application_id: int, user: User, db: AsyncSession) -> Application:
    stmt = (
        select(Application)
        .where(Application.id == application_id, Application.org_id == user.org_id)
        .options(selectinload(Application.vacancy))
    )
    app_row = (await db.execute(stmt)).scalar_one_or_none()
    if app_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return app_row


@router.get("", response_model=list[ApplicationListItem])
async def list_applications(
    vacancy_id: int | None = None,
    status_filter: ApplicationStatus | None = Query(default=None, alias="status"),
    min_score: int | None = Query(default=None, ge=0, le=100),
    sort: str = Query(default="score_desc", pattern="^(score_desc|score_asc|newest|oldest)$"),
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Application)
        .where(Application.org_id == user.org_id)
        .options(selectinload(Application.vacancy))
    )
    if vacancy_id is not None:
        stmt = stmt.where(Application.vacancy_id == vacancy_id)
    if status_filter is not None:
        stmt = stmt.where(Application.status == status_filter)
    if min_score is not None:
        stmt = stmt.where(Application.match_percentage >= min_score)

    if sort == "score_desc":
        stmt = stmt.order_by(Application.match_percentage.desc().nullslast(), Application.created_at.desc())
    elif sort == "score_asc":
        stmt = stmt.order_by(Application.match_percentage.asc().nullsfirst(), Application.created_at.desc())
    elif sort == "oldest":
        stmt = stmt.order_by(Application.created_at.asc())
    else:
        stmt = stmt.order_by(Application.created_at.desc())

    rows = (await db.execute(stmt)).scalars().all()
    # Attach candidate eagerly per row
    result = []
    for r in rows:
        cand = await db.get(Candidate, r.candidate_id) if r.candidate_id else None
        item = ApplicationListItem.model_validate(r)
        item.candidate = cand  # type: ignore[assignment]
        result.append(item)
    return result


@router.get("/{application_id}", response_model=ApplicationDetail)
async def get_application(
    application_id: int,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    app_row = await _get_owned(application_id, user, db)
    cand = await db.get(Candidate, app_row.candidate_id) if app_row.candidate_id else None
    detail = ApplicationDetail.model_validate(app_row)
    detail.candidate = cand  # type: ignore[assignment]
    return detail


@router.get("/{application_id}/resume")
async def download_resume(
    application_id: int,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    app_row = await _get_owned(application_id, user, db)
    if not app_row.file_path or not resume_exists(app_row.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume file missing")
    data = read_resume(app_row.file_path)
    filename = app_row.original_filename or "resume"
    return Response(
        content=data,
        media_type=app_row.file_mime or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.post("/{application_id}/rescore", response_model=ApplicationDetail)
async def rescore_application(
    application_id: int,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    app_row = await _get_owned(application_id, user, db)
    app_row.status = ApplicationStatus.pending
    app_row.error = None
    await db.commit()
    score_application.delay(app_row.id)
    cand = await db.get(Candidate, app_row.candidate_id) if app_row.candidate_id else None
    detail = ApplicationDetail.model_validate(app_row)
    detail.candidate = cand  # type: ignore[assignment]
    return detail


@router.patch("/{application_id}/stage", response_model=ApplicationDetail)
async def update_stage(
    application_id: int,
    payload: StageUpdate,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    app_row = await _get_owned(application_id, user, db)
    old = app_row.stage
    app_row.stage = payload.stage
    if payload.reason:
        app_row.decision_reason = payload.reason
    await log_activity(
        db,
        application=app_row,
        type=ActivityType.stage_changed,
        actor=ActivityActor.user,
        actor_user_id=user.id,
        summary=f"Stage: {old.value} → {payload.stage.value}",
        payload={"from": old.value, "to": payload.stage.value, "reason": payload.reason},
    )
    await db.commit()
    await db.refresh(app_row)
    return ApplicationDetail.model_validate(app_row)


@router.get("/{application_id}/timeline", response_model=list[ActivityOut])
async def application_timeline(
    application_id: int,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned(application_id, user, db)  # ownership check
    rows = (
        await db.execute(
            select(Activity)
            .where(Activity.application_id == application_id, Activity.org_id == user.org_id)
            .order_by(Activity.created_at.desc())
        )
    ).scalars().all()
    return rows


@router.get("/{application_id}/submissions", response_model=list[SubmissionOut])
async def list_submissions(
    application_id: int,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned(application_id, user, db)
    rows = (
        await db.execute(
            select(Submission)
            .where(Submission.application_id == application_id, Submission.org_id == user.org_id)
            .order_by(Submission.created_at.desc())
        )
    ).scalars().all()
    return rows


@router.get("/{application_id}/interviews", response_model=list[InterviewOut])
async def list_interviews(
    application_id: int,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned(application_id, user, db)
    rows = (
        await db.execute(
            select(Interview)
            .where(Interview.application_id == application_id, Interview.org_id == user.org_id)
            .order_by(Interview.scheduled_at.desc().nullslast())
        )
    ).scalars().all()
    return rows


# ---------------- Messaging (two-way thread) ----------------
@router.get("/{application_id}/messages", response_model=list[MessageOut])
async def list_messages(
    application_id: int,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned(application_id, user, db)
    rows = (
        await db.execute(
            select(Message)
            .where(Message.application_id == application_id, Message.org_id == user.org_id)
            .order_by(Message.created_at.asc())
        )
    ).scalars().all()
    return rows


@router.post("/{application_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    application_id: int,
    payload: SendMessageIn,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    app_row = await _get_owned(application_id, user, db)
    msg = await send_to_candidate(
        db, app_row, payload.body, sent_by_user_id=user.id, actor=ActivityActor.user
    )
    await db.commit()
    await db.refresh(msg)
    return msg


async def _resolve_body(db, app_row, action: str, payload: ActionIn) -> tuple[str, int | None]:
    vacancy = app_row.vacancy
    org = await db.get(Organization, app_row.org_id)
    candidate = await db.get(Candidate, app_row.candidate_id) if app_row.candidate_id else None
    ctx = build_context(
        application=app_row, vacancy=vacancy, candidate=candidate,
        organization=org, extra=payload.variables,
    )
    if payload.body is not None:
        return render(payload.body, ctx), payload.template_id

    tpl = None
    if payload.template_id:
        tpl = await db.get(MessageTemplate, payload.template_id)
        if tpl and tpl.org_id != app_row.org_id:
            tpl = None
    if tpl is None:
        ttype = _ACTIONS[action][2]
        tpl = (
            await db.execute(
                select(MessageTemplate)
                .where(MessageTemplate.org_id == app_row.org_id, MessageTemplate.type == ttype)
                .limit(1)
            )
        ).scalar_one_or_none()
    return render(tpl.body if tpl else "", ctx), (tpl.id if tpl else None)


@router.post("/{application_id}/actions/{action}", response_model=ApplicationDetail)
async def run_action(
    application_id: int,
    action: str,
    payload: ActionIn,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    """One-click recruiter action: render a template, message the candidate, advance the stage."""
    if action not in _ACTIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown action")
    app_row = await _get_owned(application_id, user, db)
    target_stage, activity_type, _ = _ACTIONS[action]

    body, template_id = await _resolve_body(db, app_row, action, payload)

    # For offers, generate a branded PDF and attach it to the Telegram message.
    document = None
    if action == "offer":
        org = await db.get(Organization, app_row.org_id)
        candidate = await db.get(Candidate, app_row.candidate_id) if app_row.candidate_id else None
        vars_ = payload.variables or {}
        pdf = generate_offer_pdf(
            company=org.name if org else "",
            candidate_name=(candidate.full_name or candidate.telegram_username or "Candidate") if candidate else "Candidate",
            job_title=app_row.vacancy.title if app_row.vacancy else "",
            body_text=body,
            salary=vars_.get("salary"),
            start_date=vars_.get("start_date"),
        )
        if pdf:
            document = (pdf, "offer-letter.pdf")

    await send_to_candidate(
        db, app_row, body,
        sent_by_user_id=user.id, template_id=template_id,
        document=document,
        activity_type=activity_type, actor=ActivityActor.user,
        activity_summary=f"{action.replace('_', ' ').title()} sent",
    )
    app_row.stage = target_stage
    if action == "reject":
        app_row.decision_reason = body[:500]
    await db.commit()

    # After sending a test task, mark the candidate as awaiting a submission so their next
    # uploaded file is captured as a graded submission (not a new application).
    if action == "test_task" and app_row.candidate_id:
        candidate = await db.get(Candidate, app_row.candidate_id)
        if candidate and candidate.telegram_user_id:
            await set_awaiting_submission(app_row.org_id, candidate.telegram_user_id, app_row.id)

    await db.refresh(app_row)
    return ApplicationDetail.model_validate(app_row)


@router.post("/upload", response_model=ApplicationDetail, status_code=status.HTTP_201_CREATED)
async def manual_upload(
    vacancy_id: int = Query(...),
    file: UploadFile = File(...),
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin-side manual resume intake (alternative to Telegram)."""
    vacancy = await db.get(Vacancy, vacancy_id)
    if vacancy is None or vacancy.org_id != user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")

    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_mb} MB",
        )

    key = save_resume(user.org_id, data, file.filename)
    app_row = Application(
        org_id=user.org_id,
        vacancy_id=vacancy.id,
        source=ApplicationSource.manual,
        original_filename=file.filename,
        file_path=key,
        file_mime=guess_mime(file.filename, file.content_type),
        status=ApplicationStatus.pending,
    )
    db.add(app_row)
    await db.commit()
    await db.refresh(app_row)
    score_application.delay(app_row.id)
    return ApplicationDetail.model_validate(app_row)
