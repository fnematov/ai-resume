from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Activity, ActivityActor, ActivityType, Application


async def log_activity(
    db: AsyncSession,
    *,
    application: Application,
    type: ActivityType,
    actor: ActivityActor = ActivityActor.system,
    actor_user_id: int | None = None,
    summary: str = "",
    payload: dict | None = None,
) -> Activity:
    """Append an entry to an application's timeline and bump last_activity_at.

    Does NOT commit — the caller controls the transaction.
    """
    activity = Activity(
        org_id=application.org_id,
        application_id=application.id,
        type=type,
        actor=actor,
        actor_user_id=actor_user_id,
        summary=summary,
        payload=payload,
    )
    db.add(activity)
    application.last_activity_at = datetime.now(timezone.utc)
    return activity
