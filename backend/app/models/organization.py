from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import AIProvider, OrgStatus
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.vacancy import Vacancy


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    status: Mapped[OrgStatus] = mapped_column(
        SAEnum(OrgStatus, name="org_status"), default=OrgStatus.pending, nullable=False
    )

    # Telegram (per-org bot). Token stored encrypted at rest.
    telegram_bot_username: Mapped[str | None] = mapped_column(String(80), nullable=True)
    telegram_bot_token_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    telegram_webhook_secret: Mapped[str | None] = mapped_column(String(80), nullable=True)

    # AI provider config (per org). Key stored encrypted at rest.
    ai_provider: Mapped[AIProvider | None] = mapped_column(
        SAEnum(AIProvider, name="ai_provider"), nullable=True
    )
    ai_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ai_api_key_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Internal language the AI writes its recruiter-facing analysis in (not shown to candidates).
    ai_language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    # Org-wide AI instructions applied to every candidate evaluation (complements per-vacancy rules).
    ai_general_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Calendly scheduling (per org). Token stored encrypted at rest.
    calendly_token_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    calendly_event_type_uri: Mapped[str | None] = mapped_column(String(255), nullable=True)
    calendly_scheduling_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    calendly_webhook_signing_key: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Company profile (shown to candidates with the vacancy)
    about: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Branding (offer letters / messages)
    logo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    brand_color: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # GDPR
    retention_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    privacy_notice: Mapped[str | None] = mapped_column(Text, nullable=True)

    users: Mapped[list["User"]] = relationship(back_populates="organization")
    vacancies: Mapped[list["Vacancy"]] = relationship(back_populates="organization")

    @property
    def telegram_configured(self) -> bool:
        return bool(self.telegram_bot_token_enc and self.telegram_bot_username)

    @property
    def ai_configured(self) -> bool:
        return bool(self.ai_provider and self.ai_api_key_enc)

    @property
    def calendly_configured(self) -> bool:
        return bool(self.calendly_token_enc and self.calendly_scheduling_url)
