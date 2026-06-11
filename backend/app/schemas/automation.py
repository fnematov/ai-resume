from pydantic import BaseModel, Field

from app.models.enums import AutomationAction


class AutomationRuleOut(BaseModel):
    id: int
    name: str
    vacancy_id: int | None
    min_score: int
    max_score: int
    action: AutomationAction
    template_id: int | None
    enabled: bool
    priority: int

    model_config = {"from_attributes": True}


class AutomationRuleCreate(BaseModel):
    name: str = ""
    vacancy_id: int | None = None
    min_score: int = Field(default=0, ge=0, le=100)
    max_score: int = Field(default=100, ge=0, le=100)
    action: AutomationAction
    template_id: int | None = None
    enabled: bool = True
    priority: int = 0


class AutomationRuleUpdate(BaseModel):
    name: str | None = None
    vacancy_id: int | None = None
    min_score: int | None = Field(default=None, ge=0, le=100)
    max_score: int | None = Field(default=None, ge=0, le=100)
    action: AutomationAction | None = None
    template_id: int | None = None
    enabled: bool | None = None
    priority: int | None = None
