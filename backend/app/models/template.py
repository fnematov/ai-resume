from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import TemplateType
from app.models.mixins import TimestampMixin


class MessageTemplate(Base, TimestampMixin):
    """Reusable message body with `{{variable}}` placeholders, per org."""

    __tablename__ = "message_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[TemplateType] = mapped_column(
        SAEnum(TemplateType, name="template_type"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
