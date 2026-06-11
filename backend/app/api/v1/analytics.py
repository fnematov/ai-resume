from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_org_user, get_superadmin
from app.models import (
    Application,
    ApplicationStatus,
    Candidate,
    Organization,
    OrgStatus,
    User,
    Vacancy,
    VacancyStatus,
)
from app.schemas.analytics import OrgDashboard, PlatformDashboard, VacancyStat
from app.schemas.application import ApplicationListItem

router = APIRouter()

_BUCKETS = [("0-20", 0, 20), ("21-40", 21, 40), ("41-60", 41, 60), ("61-80", 61, 80), ("81-100", 81, 100)]


@router.get("/dashboard", response_model=OrgDashboard)
async def org_dashboard(
    user: User = Depends(get_org_user), db: AsyncSession = Depends(get_db)
):
    org_id = user.org_id
    base = select(func.count(Application.id)).where(Application.org_id == org_id)
    total = await db.scalar(base) or 0
    scored = await db.scalar(base.where(Application.status == ApplicationStatus.scored)) or 0
    pending = await db.scalar(
        base.where(Application.status.in_([ApplicationStatus.pending, ApplicationStatus.processing]))
    ) or 0
    failed = await db.scalar(base.where(Application.status == ApplicationStatus.failed)) or 0
    avg_score = await db.scalar(
        select(func.avg(Application.match_percentage)).where(
            Application.org_id == org_id, Application.match_percentage.isnot(None)
        )
    )
    recommended = await db.scalar(
        select(func.count(Application.id)).where(
            Application.org_id == org_id,
            Application.ai_result["recommended"].astext == "true",
        )
    ) or 0
    open_vacs = await db.scalar(
        select(func.count(Vacancy.id)).where(
            Vacancy.org_id == org_id, Vacancy.status == VacancyStatus.open
        )
    ) or 0

    # Score distribution
    distribution: dict[str, int] = {}
    for label, lo, hi in _BUCKETS:
        distribution[label] = await db.scalar(
            select(func.count(Application.id)).where(
                Application.org_id == org_id,
                Application.match_percentage >= lo,
                Application.match_percentage <= hi,
            )
        ) or 0

    # Per-vacancy stats
    rec_expr = func.sum(
        case((Application.ai_result["recommended"].astext == "true", 1), else_=0)
    )
    per_vac_rows = (
        await db.execute(
            select(
                Vacancy.id,
                Vacancy.title,
                func.count(Application.id),
                func.avg(Application.match_percentage),
                rec_expr,
            )
            .select_from(Vacancy)
            .outerjoin(Application, Application.vacancy_id == Vacancy.id)
            .where(Vacancy.org_id == org_id)
            .group_by(Vacancy.id, Vacancy.title)
            .order_by(func.count(Application.id).desc())
        )
    ).all()
    per_vacancy = [
        VacancyStat(
            vacancy_id=vid,
            title=title,
            application_count=cnt or 0,
            avg_score=round(float(avg), 1) if avg is not None else None,
            recommended_count=int(rec or 0),
        )
        for vid, title, cnt, avg, rec in per_vac_rows
    ]

    # Recent
    recent_rows = (
        await db.execute(
            select(Application)
            .where(Application.org_id == org_id)
            .order_by(Application.created_at.desc())
            .limit(10)
        )
    ).scalars().all()
    recent = []
    for r in recent_rows:
        cand = await db.get(Candidate, r.candidate_id) if r.candidate_id else None
        item = ApplicationListItem.model_validate(r)
        item.candidate = cand  # type: ignore[assignment]
        recent.append(item)

    return OrgDashboard(
        total_applications=total,
        scored_applications=scored,
        pending_applications=pending,
        failed_applications=failed,
        avg_score=round(float(avg_score), 1) if avg_score is not None else None,
        recommended_count=recommended,
        open_vacancies=open_vacs,
        score_distribution=distribution,
        per_vacancy=per_vacancy,
        recent=recent,
    )


@router.get("/platform", response_model=PlatformDashboard)
async def platform_dashboard(
    _: User = Depends(get_superadmin), db: AsyncSession = Depends(get_db)
):
    async def count(model, *where):
        return await db.scalar(select(func.count(model.id)).where(*where)) or 0

    return PlatformDashboard(
        total_organizations=await count(Organization),
        pending_organizations=await count(Organization, Organization.status == OrgStatus.pending),
        active_organizations=await count(Organization, Organization.status == OrgStatus.active),
        suspended_organizations=await count(Organization, Organization.status == OrgStatus.suspended),
        total_users=await count(User),
        total_vacancies=await count(Vacancy),
        total_applications=await count(Application),
    )
