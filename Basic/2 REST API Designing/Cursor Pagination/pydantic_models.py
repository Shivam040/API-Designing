from datetime import datetime
from typing import Literal

from pydantic import BaseModel


EventStatus = Literal["pending", "completed", "failed"]

class EventResponse(BaseModel):
    id: int
    status: EventStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginationResponse(BaseModel):
    limit: int
    has_more: bool
    next_cursor: str | None


class EventListResponse(BaseModel):
    data: list[EventResponse]
    pagination: PaginationResponse

