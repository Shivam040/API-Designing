from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


EventStatus = Literal["pending", "completed", "failed"]


class EventCreate(BaseModel):
    status: EventStatus = "pending"


class EventResponse(BaseModel):
    id: int
    status: EventStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginationResponse(BaseModel):
    limit: int = Field(ge=1, le=100)
    has_more: bool
    next_cursor: str | None


class EventListResponse(BaseModel):
    data: list[EventResponse]
    pagination: PaginationResponse
