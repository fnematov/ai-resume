from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import VacancyStatus
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.organization import Organization


class Vacancy(Base, TimestampMixin):
    __tablename__ = "vacancies"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    requirements: Mapped[str] = mapped_column(Text, nullable=False, default="")
    employment_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    location: Mapped[str | None] = mapped_column(String(160), nullable=True)
    # Optional extra instructions / strict rules appended to the AI scoring prompt.
    ai_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[VacancyStatus] = mapped_column(
        SAEnum(VacancyStatus, name="vacancy_status"), default=VacancyStatus.draft, nullable=False
    )
    # Telegram deep-link payload, e.g. "job_42". Unique per org.
    deep_link_param: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    organization: Mapped["Organization"] = relationship(back_populates="vacancies")
    applications: Mapped[list["Application"]] = relationship(
        back_populates="vacancy", cascade="all, delete-orphan"
    )
