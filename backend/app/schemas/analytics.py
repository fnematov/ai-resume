from pydantic import BaseModel

from app.schemas.application import ApplicationListItem


class VacancyStat(BaseModel):
    vacancy_id: int
    title: str
    application_count: int
    avg_score: float | None
    recommended_count: int


class OrgDashboard(BaseModel):
    total_applications: int
    scored_applications: int
    pending_applications: int
    failed_applications: int
    avg_score: float | None
    recommended_count: int
    open_vacancies: int
    score_distribution: dict[str, int]  # bucket label -> count
    per_vacancy: list[VacancyStat]
    recent: list[ApplicationListItem]


class PlatformDashboard(BaseModel):
    total_organizations: int
    pending_organizations: int
    active_organizations: int
    suspended_organizations: int
    total_users: int
    total_vacancies: int
    total_applications: int
