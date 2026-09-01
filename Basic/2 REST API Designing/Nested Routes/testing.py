from fastapi.testclient import TestClient
from .architecture import app

client = TestClient(app)


def test_list_user_orders() -> None:
    response = client.get("/users/1/orders")

    assert response.status_code == 200
    assert all(
        order["user_id"] == 1
        for order in response.json()
    )


def test_create_order_for_user() -> None:
    response = client.post(
        "/users/1/orders",
        json={
            "items": [
                {
                    "product_id": 8,
                    "quantity": 1,
                }
            ]
        },
    )

    assert response.status_code == 201
    assert response.json()["user_id"] == 1
    assert response.headers["location"].startswith(
        "/users/1/orders/"
    )


def test_unknown_user_returns_404() -> None:
    response = client.get("/users/999/orders")

    assert response.status_code == 404


def test_order_from_another_user_is_not_returned() -> None:
    response = client.get("/users/2/orders/101")

    assert response.status_code == 404


def test_invalid_quantity_returns_422() -> None:
    response = client.post(
        "/users/1/orders",
        json={
            "items": [
                {
                    "product_id": 8,
                    "quantity": 0,
                }
            ]
        },
    )

    assert response.status_code == 422