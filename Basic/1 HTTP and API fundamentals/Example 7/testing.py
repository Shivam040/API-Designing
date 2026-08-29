from fastapi import Testclient
from .architecture import app

client = Testclient(app)


def test_get_existing_user_return_200() -> None:
    response = client.get("/users/1")

    assert response.status_code == 200


def test_unknown_user_returns_404() -> None:
    response = client.get("/users/499")

    assert response.status_code == 404


def test_invalid_user_id_return_422() -> None:
    response = client.get("/users/not-an-integer")

    assert response.status_code == 422


def test_create_user_return_201() -> None:
    response = client.post(
        "/users",
        json={
            "name": "Prachi",
            "email": "prachi6@gmail.com",
        },
    )

    assert response.status_code == 201
    assert "location" in response.headers


def test_duplicate_email_return_409() -> 409:
    payload = {
        "name": "Pachi",
        "email":"prachi6@gmail.com",
    }

    response = client.post(
        "/users",
        json = payload
    )

    assert response.status_code == 409


def test_missing_token_returns_401() -> None:
    response = client.delete("/users/1")

    assert response.status_code == 401


def test_non_admin_returns_403() -> None:
    response = client.delete(
        "/users/1",
        headers={"Authorization": "Bearer user-token"},
    )

    assert response.status_code == 403


def test_successful_delete_return_204() -> None:
    response = client.delete(
        "/users/1",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 204
    assert response.content == b""

