from datetime import datetime

from pydantic import BaseModel

from app.models.enums import (
    ActivityActor,
    ActivityType,
    ApplicationSource,
    ApplicationStage,
    ApplicationStatus,
)


class CandidateOut(BaseModel):
    id: int
    telegram_username: str | None
    telegram_user_id: int | None
    full_name: str | None
    email: str | None = None

    model_config = {"from_attributes": True}


class AIResult(BaseModel):
    match_percentage: int
    verdict: str = ""
    recommended: bool = False
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    strengths: list[str] = []
    concerns: list[str] = []
    summary: str = ""


class ApplicationListItem(BaseModel):
    id: int
    vacancy_id: int
    status: ApplicationStatus
    stage: ApplicationStage
    source: ApplicationSource
    match_percentage: int | None
    original_filename: str | None
    candidate: CandidateOut | None = None
    created_at: datetime
    scored_at: datetime | None = None
    last_activity_at: datetime | None = None

    model_config = {"from_attributes": True}


class ApplicationDetail(ApplicationListItem):
    ai_result: AIResult | None = None
    ai_provider: str | None = None
    error: str | None = None
    extracted_text: str | None = None
    file_mime: str | None = None
    decision_reason: str | None = None


class StageUpdate(BaseModel):
    stage: ApplicationStage
    reason: str | None = None


class SubmissionOut(BaseModel):
    id: int
    original_filename: str | None
    status: str
    ai_score: int | None
    ai_feedback: AIResult | None = None
    error: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityOut(BaseModel):
    id: int
    type: ActivityType
    actor: ActivityActor
    summary: str
    payload: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
