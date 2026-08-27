from fastapi.testclient import TestClient
from .architecture import app

client = TestClient(app)


def test_get_one_user() -> None:
    response = client.get("/users/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_unknown_user_returns_404() -> None:
    response = client.get("/users/999")
    assert response.status_code == 404


def test_get_all_users() -> None:
    response = client.get("/users")

    assert response.status_code == 200
    assert len(response.json()["data"]) == 3


def test_filter_active_users() -> None:
    response = client.get(
        "/users",
        params={"active": True},
    )

    assert response.status_code == 200
    assert all(
        user["active"] is True
        for user in response.json()["data"]
    )


def test_filter_by_department() -> None:
    response = client.get(
        "/users",
        params={"department": "Engineering"},
    )

    assert response.status_code == 200
    assert all(
        user["department"] == "Engineering"
        for user in response.json()["data"]
    )


def test_filter_by_creation_date() -> None:
    response = client.get(
        "/users",
        params={"created_at": "2026-02-01T00:00:00Z"}
    )

    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


def test_active_false_filtere_is_applied() -> None:
    response = client.get(
        "/users",
        params={"active": False},
    )

    assert response.status_code == 200
    assert all(
        user["active"] is False
        for user in response.json()["data"]
    )


def test_invalid_date_returns_422() -> None:
    response = client.get(
        "/users",
        params={"created_at": "not-a-date"},
    )

    assert response.status_code == 422

