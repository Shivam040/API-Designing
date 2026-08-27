from pydantic import BaseModel, EmailStr, Field

class EmployeeUpdate(BaseModel):
    name: str | None = Field(
        default = None,
        min_length = 2,
        max_length = 100,
    )
    email: EmailStr | None = None
    department: str | None = Field(
        default = None,
        min_length = 2,
        max_length = 100,
    )
    active: bool | None = None


class EmployeeResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    department: str
    active: bool


class EmployeeUpdateResponse(BaseModel):
    employee: EmployeeResponse
    notification_requested: bool

