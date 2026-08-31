from typing import Literal

from pydantic import BaseModel, Field


Priority = Literal["low", "medium", "high"]


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    priority: Priority = "medium"
    completed: bool = False


class TaskReplace(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    priority: Priority
    completed: bool


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    priority: Priority | None = None
    completed: bool | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    priority: Priority
    completed: bool


class TaskListResponse(BaseModel):
    data: list[TaskResponse]
    limit: int
    offset: int
    returned: int

