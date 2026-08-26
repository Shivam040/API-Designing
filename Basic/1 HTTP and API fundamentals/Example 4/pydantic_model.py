from typing import Literal
from pydantic import BaseModel, Field

class PaymentCreate(BaseModel):
    order_id: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0)
    currency: Literal["INR", "USD", "EUR"]


class PaymentResponse(BaseModel):
    payment_id: str
    order_id: str
    amount: float
    currency: str
    status: str