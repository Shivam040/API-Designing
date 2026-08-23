from fastapi.testclient import TestClient
from .Architecture import app

client = TestClient(app)

def test_create_user() -> None:
    response = client.post(
        "/users/",
        json={
            "name": "Aman",
            "email": "aman@gmail.com",
            "active": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "aman@gmail.com"
    assert "location" in response.headers


def test_patch_preserves_unspecfied_fields() -> None:
    original_user = client.get("/users/1").json()
    response = client.patch(
        "/users/1",
        json={"active": False},
    )

    assert response.status_code == 200
    assert response.json()["name"] == original_user["name"]
    assert response.json()["active"] is False


def test_delete_user() -> None:
    response = client.delete("/users/1")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/users/1").status_code == 404