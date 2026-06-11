from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.security import ACCESS, decode_token
from app.models import Organization, OrgStatus, User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
    except ValueError:
        raise _CREDENTIALS_EXC
    if payload.get("type") != ACCESS:
        raise _CREDENTIALS_EXC
    user_id = payload.get("sub")
    if user_id is None:
        raise _CREDENTIALS_EXC
    user = await db.get(User, int(user_id))
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXC
    return user


def require_role(*roles: UserRole) -> Callable:
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return checker


async def get_superadmin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super-admin only")
    return user


async def get_org_user(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """A user that belongs to an *active* organization."""
    if user.role == UserRole.superadmin or user.org_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Organization account required"
        )
    org = await db.get(Organization, user.org_id)
    if org is None or org.status != OrgStatus.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your organization is not active yet. Awaiting approval.",
        )
    return user


async def get_current_org(
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    org = await db.get(Organization, user.org_id)
    assert org is not None  # guaranteed active by get_org_user
    return org
