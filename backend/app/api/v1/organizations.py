from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import (
    get_current_org,
    get_org_user,
    get_superadmin,
    get_user_org_any_status,
)
from app.core.security import encrypt_secret
from app.core.utils import random_token
from app.models import Organization, OrgStatus, User, Vacancy
from app.schemas.organization import (
    AISettingsIn,
    GdprSettingsIn,
    OrganizationAdminOut,
    OrganizationOut,
    OrgStatusUpdate,
    TelegramSettingsIn,
)
from app.services.telegram import TelegramClient, TelegramError

router = APIRouter()


def _webhook_url(org_id: int) -> str:
    base = settings.public_base_url.rstrip("/")
    return f"{base}{settings.api_v1_prefix}/telegram/webhook/{org_id}"


async def _register_webhook(org: Organization, token: str, db: AsyncSession) -> None:
    """(Re)register this org's Telegram webhook. Requires a publicly reachable HTTPS URL."""
    if not org.telegram_webhook_secret:
        org.telegram_webhook_secret = random_token(24)
    client = TelegramClient(token)
    await client.set_webhook(_webhook_url(org.id), org.telegram_webhook_secret)


# ---------------- Org-side: my organization ----------------
@router.get("/me", response_model=OrganizationOut)
async def my_organization(org: Organization = Depends(get_user_org_any_status)):
    # Accessible to pending orgs so the panel can show the awaiting-approval banner.
    return org


@router.put("/me/telegram", response_model=OrganizationOut)
async def set_telegram(
    payload: TelegramSettingsIn,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    client = TelegramClient(payload.bot_token)
    try:
        me = await client.get_me()
    except TelegramError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    org.telegram_bot_token_enc = encrypt_secret(payload.bot_token)
    org.telegram_bot_username = me.get("username")
    try:
        await _register_webhook(org, payload.bot_token, db)
    except TelegramError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bot saved but webhook registration failed: {exc}",
        )
    await db.commit()
    await db.refresh(org)
    return org


@router.put("/me/gdpr", response_model=OrganizationOut)
async def set_gdpr(
    payload: GdprSettingsIn,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    org.retention_days = payload.retention_days
    org.privacy_notice = payload.privacy_notice
    await db.commit()
    await db.refresh(org)
    return org


@router.put("/me/ai", response_model=OrganizationOut)
async def set_ai(
    payload: AISettingsIn,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    if payload.api_key:
        org.ai_api_key_enc = encrypt_secret(payload.api_key)
    elif not org.ai_api_key_enc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="An API key is required"
        )
    org.ai_provider = payload.provider
    org.ai_model = payload.model
    await db.commit()
    await db.refresh(org)
    return org


# ---------------- Super-admin: moderation ----------------
async def _to_admin_out(org: Organization, db: AsyncSession) -> OrganizationAdminOut:
    users = await db.scalar(select(func.count(User.id)).where(User.org_id == org.id))
    vacs = await db.scalar(select(func.count(Vacancy.id)).where(Vacancy.org_id == org.id))
    out = OrganizationAdminOut.model_validate(org)
    out.user_count = users or 0
    out.vacancy_count = vacs or 0
    return out


@router.get("", response_model=list[OrganizationAdminOut])
async def list_organizations(
    status_filter: OrgStatus | None = None,
    _: User = Depends(get_superadmin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Organization).order_by(Organization.created_at.desc())
    if status_filter:
        stmt = stmt.where(Organization.status == status_filter)
    orgs = (await db.execute(stmt)).scalars().all()
    return [await _to_admin_out(o, db) for o in orgs]


@router.patch("/{org_id}/status", response_model=OrganizationAdminOut)
async def update_org_status(
    org_id: int,
    payload: OrgStatusUpdate,
    _: User = Depends(get_superadmin),
    db: AsyncSession = Depends(get_db),
):
    org = await db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    org.status = payload.status
    await db.commit()
    await db.refresh(org)
    return await _to_admin_out(org, db)
