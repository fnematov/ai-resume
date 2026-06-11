from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import ApplicationSource, ApplicationStage, ApplicationStatus
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.vacancy import Vacancy


class Application(Base, TimestampMixin):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[int] = mapped_column(
        ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source: Mapped[ApplicationSource] = mapped_column(
        SAEnum(ApplicationSource, name="application_source"),
        default=ApplicationSource.telegram,
        nullable=False,
    )

    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_mime: Mapped[str | None] = mapped_column(String(120), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus, name="application_status"),
        default=ApplicationStatus.pending,
        nullable=False,
        index=True,
    )
    # Pipeline position (orthogonal to scoring `status`).
    stage: Mapped[ApplicationStage] = mapped_column(
        SAEnum(ApplicationStage, name="application_stage"),
        default=ApplicationStage.new,
        nullable=False,
        index=True,
    )
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # 0..100; nullable until scored. Indexed for ranking.
    match_percentage: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    ai_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_provider: Mapped[str | None] = mapped_column(String(40), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    vacancy: Mapped["Vacancy"] = relationship(back_populates="applications")
    candidate: Mapped["Candidate | None"] = relationship(lazy="selectin")
