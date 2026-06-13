from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.security import (
    REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.utils import slugify
from app.models import Organization, OrgStatus, User, UserRole
from app.schemas.auth import (
    ChangePassword,
    LoginResponse,
    RefreshRequest,
    RegisterOrganization,
    Token,
    UpdateMe,
    UserOut,
)

router = APIRouter()


async def _unique_slug(db: AsyncSession, name: str) -> str:
    base = slugify(name)
    slug = base
    i = 1
    while (await db.execute(select(Organization).where(Organization.slug == slug))).scalar_one_or_none():
        i += 1
        slug = f"{base}-{i}"
    return slug


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_organization(payload: RegisterOrganization, db: AsyncSession = Depends(get_db)):
    """Public self-service signup. Creates a PENDING org + its first org_admin user."""
    existing = (
        await db.execute(select(User).where(User.email == payload.email))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    org = Organization(
        name=payload.organization_name,
        slug=await _unique_slug(db, payload.organization_name),
        status=OrgStatus.pending,
    )
    db.add(org)
    await db.flush()

    user = User(
        org_id=org.id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.org_admin,
    )
    db.add(user)
    await db.flush()
    org.created_by = user.id
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user = (
        await db.execute(select(User).where(User.email == form.username))
    ).scalar_one_or_none()
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    return LoginResponse(
        access_token=create_access_token(user.id, user.role.value, user.org_id),
        refresh_token=create_refresh_token(user.id),
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=Token)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        data = decode_token(payload.refresh_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if data.get("type") != REFRESH:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    user = await db.get(User, int(data["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return Token(
        access_token=create_access_token(user.id, user.role.value, user.org_id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UpdateMe,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user.full_name = payload.full_name
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/change-password")
async def change_password(
    payload: ChangePassword,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect"
        )
    user.password_hash = hash_password(payload.new_password)
    await db.commit()
    return {"ok": True}
