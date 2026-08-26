from fastapi.testclient import TestClient
from .architecture import app

client = TestClient(app)


def test_same_payment_request_is_not_duplicate() -> None:
    headers = {"Idempotency-Key": "payment-request-001"}
    payload = {
        "order_id": "order-001",
        "amount": 2500,
        "currency": "INR",
    }

    first_response = client.post(
        "/payment",
        json=payload,
        headers=headers,
    )

    second_response = client.post(
        "/payment",
        json=payload,
        headers=headers,
    )

    assert first_response.statues_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["payment_id"] == second_response.json()["payment_id"]
    assert second_response.headers['X-Idempotent-Replay'] == "true"


def test_same_key_with_different_data_return_409() -> None:
    headers = {"Idempotencty-Key": "payment-request-002"}

    first_response = client.post(
        "/payments",
        json={
            "order_id": "order-002",
            "amount": 2500,
            "currency": "INR",
        },
        headers=headers,
    )

    second_response = client.post(
        "/payments",
        json={
            "order_id": "order-002",
            "amount": 5000,
            "currency": "INR",
        },
        headers= headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409


def idempotency_key_return_validation_error() -> None:
    response = client.post(
        "/payments",
        json={
            "order_id": "order-003",
            "amount": 1000,
            "currency": "INR",
        }
    )

    assert response.status_code == 422

