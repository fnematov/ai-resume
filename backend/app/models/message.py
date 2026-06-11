from sqlalchemy import BigInteger, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import MessageChannel, MessageDirection, MessageStatus
from app.models.mixins import TimestampMixin


class Message(Base, TimestampMixin):
    """A single message in the two-way conversation tied to an application."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    direction: Mapped[MessageDirection] = mapped_column(
        SAEnum(MessageDirection, name="message_direction"), nullable=False
    )
    channel: Mapped[MessageChannel] = mapped_column(
        SAEnum(MessageChannel, name="message_channel"), default=MessageChannel.telegram, nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("message_templates.id", ondelete="SET NULL"), nullable=True
    )
    sent_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    telegram_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[MessageStatus] = mapped_column(
        SAEnum(MessageStatus, name="message_status"), default=MessageStatus.sent, nullable=False
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
