from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Application, Candidate, Submission
from app.services.storage import delete_resume


async def erase_candidate(db: AsyncSession, candidate: Candidate) -> None:
    """Right to erasure: delete a candidate's files, applications, and PII.

    Cascades (messages, activities, submissions, interviews) are removed with the applications.
    Does NOT commit — caller controls the transaction.
    """
    apps = (
        await db.execute(select(Application).where(Application.candidate_id == candidate.id))
    ).scalars().all()
    for app_row in apps:
        delete_resume(app_row.file_path)
        subs = (
            await db.execute(select(Submission).where(Submission.application_id == app_row.id))
        ).scalars().all()
        for sub in subs:
            delete_resume(sub.file_path)
        await db.delete(app_row)
    await db.delete(candidate)


def compute_delete_after(retention_days: int | None) -> datetime | None:
    if not retention_days or retention_days <= 0:
        return None
    return datetime.now(timezone.utc) + timedelta(days=retention_days)


async def purge_expired(db: AsyncSession) -> int:
    """Erase candidates whose retention window has elapsed. Returns the count erased."""
    now = datetime.now(timezone.utc)
    expired = (
        await db.execute(
            select(Candidate).where(
                Candidate.delete_after.isnot(None), Candidate.delete_after <= now
            )
        )
    ).scalars().all()
    for candidate in expired:
        await erase_candidate(db, candidate)
    await db.commit()
    return len(expired)
