from datetime import datetime

from pydantic import BaseModel

from app.models.enums import MessageDirection, MessageStatus, TemplateType


class TemplateOut(BaseModel):
    id: int
    type: TemplateType
    name: str
    body: str
    is_default: bool

    model_config = {"from_attributes": True}


class TemplateCreate(BaseModel):
    type: TemplateType
    name: str
    body: str


class TemplateUpdate(BaseModel):
    name: str | None = None
    body: str | None = None


class MessageOut(BaseModel):
    id: int
    direction: MessageDirection
    body: str
    status: MessageStatus
    error: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageIn(BaseModel):
    body: str


class ActionIn(BaseModel):
    """Payload for one-click stage actions (test task / interview / offer / reject)."""

    template_id: int | None = None
    body: str | None = None  # overrides/edited template body (already rendered or raw)
    variables: dict[str, str] | None = None  # extra context for rendering (e.g. test_task, deadline)
