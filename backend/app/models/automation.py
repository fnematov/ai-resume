from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import AutomationAction, AutomationTrigger
from app.models.mixins import TimestampMixin


class AutomationRule(Base, TimestampMixin):
    """Score-based rule evaluated after AI scoring (hybrid automation)."""

    __tablename__ = "automation_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # NULL vacancy_id => applies to all of the org's vacancies.
    vacancy_id: Mapped[int | None] = mapped_column(
        ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    trigger: Mapped[AutomationTrigger] = mapped_column(
        SAEnum(AutomationTrigger, name="automation_trigger"),
        default=AutomationTrigger.on_scored,
        nullable=False,
    )
    # Score window [min_score, max_score] that activates the rule.
    min_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    action: Mapped[AutomationAction] = mapped_column(
        SAEnum(AutomationAction, name="automation_action"), nullable=False
    )
    # Template to send when action == send_template (or alongside reject/shortlist).
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("message_templates.id", ondelete="SET NULL"), nullable=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
