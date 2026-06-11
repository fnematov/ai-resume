from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_org_user
from app.models import MessageTemplate, User
from app.schemas.messaging import TemplateCreate, TemplateOut, TemplateUpdate
from app.services.messaging.defaults import DEFAULT_TEMPLATES

router = APIRouter()


async def _seed_defaults_if_empty(db: AsyncSession, org_id: int) -> None:
    count = await db.scalar(
        select(func.count(MessageTemplate.id)).where(MessageTemplate.org_id == org_id)
    )
    if count:
        return
    for t in DEFAULT_TEMPLATES:
        db.add(
            MessageTemplate(
                org_id=org_id, type=t["type"], name=t["name"], body=t["body"], is_default=True
            )
        )
    await db.commit()


@router.get("", response_model=list[TemplateOut])
async def list_templates(
    user: User = Depends(get_org_user), db: AsyncSession = Depends(get_db)
):
    await _seed_defaults_if_empty(db, user.org_id)
    rows = (
        await db.execute(
            select(MessageTemplate)
            .where(MessageTemplate.org_id == user.org_id)
            .order_by(MessageTemplate.type, MessageTemplate.id)
        )
    ).scalars().all()
    return rows


@router.post("", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: TemplateCreate,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    tpl = MessageTemplate(
        org_id=user.org_id, type=payload.type, name=payload.name, body=payload.body
    )
    db.add(tpl)
    await db.commit()
    await db.refresh(tpl)
    return tpl


@router.patch("/{template_id}", response_model=TemplateOut)
async def update_template(
    template_id: int,
    payload: TemplateUpdate,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    tpl = await db.get(MessageTemplate, template_id)
    if tpl is None or tpl.org_id != user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tpl, field, value)
    await db.commit()
    await db.refresh(tpl)
    return tpl


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    tpl = await db.get(MessageTemplate, template_id)
    if tpl is None or tpl.org_id != user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    await db.delete(tpl)
    await db.commit()
