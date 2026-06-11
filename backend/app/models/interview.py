from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import InterviewProvider, InterviewStatus
from app.models.mixins import TimestampMixin


class Interview(Base, TimestampMixin):
    """A scheduled interview, typically booked through Calendly."""

    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[InterviewProvider] = mapped_column(
        SAEnum(InterviewProvider, name="interview_provider"),
        default=InterviewProvider.calendly,
        nullable=False,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    join_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    location: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[InterviewStatus] = mapped_column(
        SAEnum(InterviewStatus, name="interview_status"),
        default=InterviewStatus.scheduled,
        nullable=False,
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    raw: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
