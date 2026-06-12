from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_org, get_org_user
from app.models import Application, Organization, User, Vacancy, VacancyStatus
from app.schemas.vacancy import VacancyCreate, VacancyOut, VacancyUpdate

router = APIRouter()


def _deep_link_url(org: Organization, vacancy: Vacancy) -> str | None:
    if org.telegram_bot_username and vacancy.deep_link_param:
        return f"https://t.me/{org.telegram_bot_username}?start={vacancy.deep_link_param}"
    return None


async def _to_out(vacancy: Vacancy, org: Organization, db: AsyncSession) -> VacancyOut:
    count = await db.scalar(
        select(func.count(Application.id)).where(Application.vacancy_id == vacancy.id)
    )
    out = VacancyOut.model_validate(vacancy)
    out.application_count = count or 0
    out.deep_link_url = _deep_link_url(org, vacancy)
    return out


@router.get("", response_model=list[VacancyOut])
async def list_vacancies(
    status_filter: VacancyStatus | None = None,
    user: User = Depends(get_org_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Vacancy).where(Vacancy.org_id == user.org_id).order_by(Vacancy.created_at.desc())
    if status_filter:
        stmt = stmt.where(Vacancy.status == status_filter)
    rows = (await db.execute(stmt)).scalars().all()
    return [await _to_out(v, org, db) for v in rows]


@router.post("", response_model=VacancyOut, status_code=status.HTTP_201_CREATED)
async def create_vacancy(
    payload: VacancyCreate,
    user: User = Depends(get_org_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    vacancy = Vacancy(
        org_id=user.org_id,
        created_by=user.id,
        title=payload.title,
        description=payload.description,
        requirements=payload.requirements,
        employment_type=payload.employment_type,
        location=payload.location,
        ai_instructions=payload.ai_instructions,
        status=payload.status,
    )
    db.add(vacancy)
    await db.flush()
    # Deep-link payload is derived from the id once it exists.
    vacancy.deep_link_param = f"job_{vacancy.id}"
    await db.commit()
    await db.refresh(vacancy)
    return await _to_out(vacancy, org, db)


async def _get_owned(vacancy_id: int, user: User, db: AsyncSession) -> Vacancy:
    vacancy = await db.get(Vacancy, vacancy_id)
    if vacancy is None or vacancy.org_id != user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    return vacancy


@router.get("/{vacancy_id}", response_model=VacancyOut)
async def get_vacancy(
    vacancy_id: int,
    user: User = Depends(get_org_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    vacancy = await _get_owned(vacancy_id, user, db)
    return await _to_out(vacancy, org, db)


@router.patch("/{vacancy_id}", response_model=VacancyOut)
async def update_vacancy(
    vacancy_id: int,
    payload: VacancyUpdate,
    user: User = Depends(get_org_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    vacancy = await _get_owned(vacancy_id, user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(vacancy, field, value)
    await db.commit()
    await db.refresh(vacancy)
    return await _to_out(vacancy, org, db)


@router.delete("/{vacancy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vacancy(
    vacancy_id: int,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    vacancy = await _get_owned(vacancy_id, user, db)
    await db.delete(vacancy)
    await db.commit()
