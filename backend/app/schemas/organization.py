from pydantic import BaseModel, Field

from app.models.enums import AIProvider, OrgStatus


class OrganizationOut(BaseModel):
    id: int
    name: str
    slug: str
    status: OrgStatus
    telegram_bot_username: str | None
    telegram_configured: bool
    ai_provider: AIProvider | None
    ai_model: str | None
    ai_configured: bool
    calendly_configured: bool = False
    calendly_scheduling_url: str | None = None
    retention_days: int | None = None
    privacy_notice: str | None = None
    about: str | None = None
    website: str | None = None

    model_config = {"from_attributes": True}


class OrganizationAdminOut(OrganizationOut):
    """Super-admin listing view with extra counts."""

    user_count: int = 0
    vacancy_count: int = 0


class TelegramSettingsIn(BaseModel):
    bot_token: str = Field(min_length=20, description="Telegram bot token from @BotFather")


class AISettingsIn(BaseModel):
    provider: AIProvider
    model: str = Field(min_length=2, max_length=120)
    # Optional on update: blank keeps the existing key (write-only).
    api_key: str | None = None


class OrgStatusUpdate(BaseModel):
    status: OrgStatus


class GdprSettingsIn(BaseModel):
    retention_days: int | None = None
    privacy_notice: str | None = None


class ProfileSettingsIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    about: str | None = Field(default=None, max_length=512)
    website: str | None = Field(default=None, max_length=255)
