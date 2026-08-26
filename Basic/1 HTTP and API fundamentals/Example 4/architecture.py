import hashlib
import json
from typing import Annotated
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Response, status, Header
from .pydantic_model import PaymentCreate, PaymentResponse

app = FastAPI()

idempotency_records: dict[str, dict] = {}


def create_request_hash(payload: PaymentCreate) -> str:
    normalized_payload = json.dump(
        payload.model_dump(),
        sort_keys=True,
    )
    return hashlib.sha256(normalized_payload.encode()).hexdigest()


@app.post("/payments",
          model_response=PaymentCreate,
          status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    response: Response,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=100),],
) -> PaymentResponse:
    request_hash = create_request_hash(payload)
    existing_record=idempotency_key.get(request_hash)

    if existing_record is not None:
        if existing_record["request_hash"] != request_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                details=(
                    "Idempotency key was already used",
                    "with different request data"
                ),
            )

        response.status_code = status.HTTP_200_OK
        response.headers["X-Idempotant-Replay"] = "true"

        return PaymentResponse(**existing_record["response"])


    payment = PaymentResponse(
        payment_id=f"payment-{uuid4().hex[:8]}",
        order_id=payload.order_id,
        amount=payload.amount,
        currency=payload.currency,
        status="completed",
    )

    idempotency_records[idempotency_key] = {
        "request_hash": request_hash,
        "response": payment.model_dump(),
    }

    response.headers["X-Idempotent-Replay"] = "false"
    return payment
