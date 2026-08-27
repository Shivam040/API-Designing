from datetime import datetime
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: int
    name: str
    department: str
    active: bool
    created_at: datetime


class PaginationResponse(BaseModel):
    limit: int
    offset: int
    returned: int


class UserListResponse:
    data: list[UserResponse]
    pagination: PaginationResponse

    