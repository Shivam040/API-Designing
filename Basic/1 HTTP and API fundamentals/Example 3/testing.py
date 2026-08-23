from fastapi.testclient import TestClient

from .architecture import app


client = TestClient(app)


def test_get_does_not_modify_user() -> None:
    first_response = client.get("/users/1")
    second_response = client.get("/users/1")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json() == second_response.json()


def test_put_is_idempotent() -> None:
    payload = {
        "name": "Neha Sharma",
        "active": False,
    }

    first_response = client.put("/users/1", json=payload)
    second_response = client.put("/users/1", json=payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json() == second_response.json()


def test_delete_final_state_is_idempotent() -> None:
    first_response = client.delete("/users/1")
    second_response = client.delete("/users/1")

    assert first_response.status_code == 200
    assert second_response.status_code == 404
    assert client.get("/users/1").status_code == 404


def test_post_can_create_multiple_resources() -> None:
    first_response = client.post("/users",
                                 json={"name": "Ankita"},)
    second_response = client.post("/users",
                                  json={"name": "Ankita"},)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["id"] != second_response.json()["id"]

