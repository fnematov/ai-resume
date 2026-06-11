from datetime import datetime

from pydantic import BaseModel


class CalendlyConnectIn(BaseModel):
    token: str
    event_type_uri: str
    scheduling_url: str


class CalendlyTokenIn(BaseModel):
    token: str


class EventTypeOut(BaseModel):
    uri: str
    name: str
    scheduling_url: str
    duration: int | None = None


class InterviewOut(BaseModel):
    id: int
    provider: str
    scheduled_at: datetime | None
    end_at: datetime | None
    join_url: str | None
    location: str | None
    status: str

    model_config = {"from_attributes": True}
