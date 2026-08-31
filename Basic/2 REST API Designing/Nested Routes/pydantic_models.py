from typing import Literal
from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    pruduct: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)


class OrderCreate(BaseModel):
    item: list[OrderItemCreate] = Field(min_length=1)


class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: Literal["pending", "confirmed", "cancelled"]
    items: list[OrderItemCreate]

