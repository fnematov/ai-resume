from pydantic import BaseModel, Field

from app.models.enums import VacancyStatus


class VacancyBase(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = ""
    requirements: str = ""
    employment_type: str | None = None
    location: str | None = None
    ai_instructions: str | None = None


class VacancyCreate(VacancyBase):
    status: VacancyStatus = VacancyStatus.draft


class VacancyUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    requirements: str | None = None
    employment_type: str | None = None
    location: str | None = None
    ai_instructions: str | None = None
    status: VacancyStatus | None = None


class VacancyOut(VacancyBase):
    id: int
    org_id: int
    status: VacancyStatus
    deep_link_param: str | None
    deep_link_url: str | None = None
    application_count: int = 0
    has_image: bool = False

    model_config = {"from_attributes": True}
