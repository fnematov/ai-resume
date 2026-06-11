from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models import User, UserRole


async def seed_superadmin(db: AsyncSession) -> None:
    """Create the platform super-admin on first boot if it doesn't exist."""
    existing = (
        await db.execute(select(User).where(User.email == settings.superadmin_email))
    ).scalar_one_or_none()
    if existing:
        return
    db.add(
        User(
            org_id=None,
            email=settings.superadmin_email,
            password_hash=hash_password(settings.superadmin_password),
            full_name=settings.superadmin_name,
            role=UserRole.superadmin,
            is_active=True,
        )
    )
    await db.commit()
