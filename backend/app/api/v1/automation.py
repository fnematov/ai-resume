from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_org_user
from app.models import AutomationRule, User
from app.schemas.automation import (
    AutomationRuleCreate,
    AutomationRuleOut,
    AutomationRuleUpdate,
)

router = APIRouter()


@router.get("", response_model=list[AutomationRuleOut])
async def list_rules(user: User = Depends(get_org_user), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(AutomationRule)
            .where(AutomationRule.org_id == user.org_id)
            .order_by(AutomationRule.priority.desc(), AutomationRule.id)
        )
    ).scalars().all()
    return rows


@router.post("", response_model=AutomationRuleOut, status_code=status.HTTP_201_CREATED)
async def create_rule(
    payload: AutomationRuleCreate,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    rule = AutomationRule(org_id=user.org_id, **payload.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.patch("/{rule_id}", response_model=AutomationRuleOut)
async def update_rule(
    rule_id: int,
    payload: AutomationRuleUpdate,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    rule = await db.get(AutomationRule, rule_id)
    if rule is None or rule.org_id != user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int,
    user: User = Depends(get_org_user),
    db: AsyncSession = Depends(get_db),
):
    rule = await db.get(AutomationRule, rule_id)
    if rule is None or rule.org_id != user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
