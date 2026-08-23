from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    active: bool = True

class UserReplace(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    active: bool

class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    active: bool | None = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    active: bool