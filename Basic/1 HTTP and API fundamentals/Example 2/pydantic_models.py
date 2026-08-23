from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str


class UserReplace(BaseModel):
    name: str
    active: bool
