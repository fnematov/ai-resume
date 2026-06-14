import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.security import decrypt_secret
from app.models import (
    ActivityActor,
    ActivityType,
    Application,
    ApplicationStage,
    ApplicationStatus,
    Organization,
    Submission,
    SubmissionStatus,
    Vacancy,
)
from app.services.activities import log_activity
from app.services.ai import get_provider
from app.services.ai.base import JobSpec, ResumeDocument
from app.services.extraction import normalize_document
from app.services.storage import read_resume
from app.workers.celery_app import celery_app


async def _score(application_id: int) -> None:
    # Each Celery task runs in a fresh event loop (asyncio.run). A pooled engine
    # binds connections to the loop that created them, so we build a short-lived
    # NullPool engine per task and dispose it — avoiding "Future attached to a
    # different loop" errors.
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    try:
        await _run_score(SessionLocal, application_id)
    finally:
        await engine.dispose()


async def _run_score(SessionLocal, application_id: int) -> None:
    async with SessionLocal() as db:
        app_row = await db.get(Application, application_id)
        if app_row is None:
            return
        app_row.status = ApplicationStatus.processing
        app_row.error = None
        await db.commit()

        vacancy = await db.get(Vacancy, app_row.vacancy_id)
        org = await db.get(Organization, app_row.org_id)

        try:
            if org is None or not org.ai_configured:
                raise RuntimeError("Organization has no AI provider configured")
            if vacancy is None:
                raise RuntimeError("Vacancy not found")
            if not app_row.file_path:
                raise RuntimeError("No resume file attached")

            data = read_resume(app_row.file_path)
            document = normalize_document(data, app_row.original_filename, app_row.file_mime)
            if document.text and not app_row.extracted_text:
                app_row.extracted_text = document.text[:200_000]

            # Fold in the cover letter (text or file) so the AI factors it into the score.
            cover_text = app_row.cover_letter_text
            if not cover_text and app_row.cover_letter_file_path:
                cl_data = read_resume(app_row.cover_letter_file_path)
                cover_doc = normalize_document(
                    cl_data, app_row.cover_letter_filename, app_row.cover_letter_mime
                )
                cover_text = cover_doc.text
            if cover_text:
                prefix = (document.text + "\n\n") if document.text else ""
                document.text = f"{prefix}=== COVER LETTER ===\n{cover_text.strip()}"

            api_key = decrypt_secret(org.ai_api_key_enc)  # type: ignore[arg-type]
            provider = get_provider(org.ai_provider, api_key, org.ai_model)  # type: ignore[arg-type]
            job = JobSpec(
                title=vacancy.title,
                description=vacancy.description,
                requirements=vacancy.requirements,
                employment_type=vacancy.employment_type,
                location=vacancy.location,
                ai_instructions=vacancy.ai_instructions,
            )
            # The recruiter-facing analysis is written in the org's internal AI language
            # (candidate-facing messages still use the candidate's chosen language).
            language = org.ai_language or "uz"
            result = await provider.score_resume(job, document, language, org.ai_general_prompt)

            app_row.ai_result = result.to_dict()
            app_row.match_percentage = result.match_percentage
            app_row.ai_provider = org.ai_provider.value if org.ai_provider else None
            app_row.status = ApplicationStatus.scored
            app_row.scored_at = datetime.now(timezone.utc)
            # Move a brand-new application into the screening stage once scored.
            if app_row.stage == ApplicationStage.new:
                app_row.stage = ApplicationStage.screening
            await log_activity(
                db,
                application=app_row,
                type=ActivityType.ai_scored,
                actor=ActivityActor.system,
                summary=f"AI score: {result.match_percentage}% — {result.verdict}",
                payload={"match_percentage": result.match_percentage, "recommended": result.recommended},
            )
            await db.commit()
            # Hybrid automation: apply score-based rules now that a score exists.
            from app.services.automation import run_automation_for_application

            await run_automation_for_application(db, app_row.id)
        except Exception as exc:  # noqa: BLE001 - persist any failure for visibility
            app_row.status = ApplicationStatus.failed
            app_row.error = str(exc)[:2000]
            await db.commit()


@celery_app.task(name="score_application", bind=True, max_retries=2, default_retry_delay=30)
def score_application(self, application_id: int) -> None:
    """Extract → score → persist. Runs the async pipeline in a fresh event loop."""
    asyncio.run(_score(application_id))


async def _evaluate(submission_id: int) -> None:
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with SessionLocal() as db:
            sub = await db.get(Submission, submission_id)
            if sub is None:
                return
            sub.status = SubmissionStatus.processing
            await db.commit()

            app_row = await db.get(Application, sub.application_id)
            vacancy = await db.get(Vacancy, app_row.vacancy_id) if app_row else None
            org = await db.get(Organization, sub.org_id)
            try:
                if org is None or not org.ai_configured:
                    raise RuntimeError("Organization has no AI provider configured")
                if vacancy is None:
                    raise RuntimeError("Vacancy not found")

                if sub.file_path:
                    data = read_resume(sub.file_path)
                    document = normalize_document(data, sub.original_filename, sub.file_mime)
                else:
                    document = ResumeDocument(text=sub.text or "(empty submission)")

                api_key = decrypt_secret(org.ai_api_key_enc)  # type: ignore[arg-type]
                provider = get_provider(org.ai_provider, api_key, org.ai_model)  # type: ignore[arg-type]
                job = JobSpec(
                    title=vacancy.title,
                    description=vacancy.description,
                    requirements=vacancy.requirements,
                )
                language = org.ai_language or "uz"
                result = await provider.evaluate_submission(
                    job, document, sub.instructions or "", sub.criteria or "", language, org.ai_general_prompt
                )
                sub.ai_score = result.match_percentage
                sub.ai_feedback = result.to_dict()
                sub.status = SubmissionStatus.graded
                if app_row is not None:
                    await log_activity(
                        db,
                        application=app_row,
                        type=ActivityType.test_graded,
                        actor=ActivityActor.system,
                        summary=f"Test task graded: {result.match_percentage}% — {result.verdict}",
                    )
            except Exception as exc:  # noqa: BLE001
                sub.status = SubmissionStatus.failed
                sub.error = str(exc)[:2000]
            await db.commit()
    finally:
        await engine.dispose()


@celery_app.task(name="evaluate_submission", bind=True, max_retries=2, default_retry_delay=30)
def evaluate_submission(self, submission_id: int) -> None:
    """Grade a candidate's test-task submission against the task criteria."""
    asyncio.run(_evaluate(submission_id))


async def _purge() -> None:
    from app.services.gdpr import purge_expired

    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with SessionLocal() as db:
            await purge_expired(db)
    finally:
        await engine.dispose()


@celery_app.task(name="purge_expired_candidates")
def purge_expired_candidates() -> None:
    """GDPR retention: erase candidates whose retention window has elapsed."""
    asyncio.run(_purge())
