from sqlalchemy import Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import ActivityActor, ActivityType
from app.models.mixins import TimestampMixin


class Activity(Base, TimestampMixin):
    """Append-only timeline of everything that happens to an application."""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[ActivityType] = mapped_column(
        SAEnum(ActivityType, name="activity_type"), nullable=False
    )
    actor: Mapped[ActivityActor] = mapped_column(
        SAEnum(ActivityActor, name="activity_actor"), default=ActivityActor.system, nullable=False
    )
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    summary: Mapped[str] = mapped_column(String(400), nullable=False, default="")
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
