from fastapi.testclient import TestClient
from .architecture import app

client = TestClient(app)


def test_create_task_returns_201() -> None:
    response = client.post(
        "/tasks",
        json={
            "title": "Prepare FastAPI interview",
            "completed": False,
        },
    )

    assert response.status_code == 201
    assert response.headers["location"].startswith("/tasks/")


def test_get_task_returns_200() -> None:
    created = client.post(
        "/tasks",
        json={"title": "Study REST"},
    ).json()

    response = client.get(f"/tasks/{created['id']}")

    assert response.status_code == 200
    assert response.json()["title"] == "Study REST"


def test_filter_completed_tasks() -> None:
    response = client.get(
        "/tasks",
        params={"completed": False},
    )

    assert response.status_code == 200
    assert all(
        task["completed"] is False
        for task in response.json()
    )


def test_unknown_task_returns_404() -> None:
    response = client.get("/tasks/999")

    assert response.status_code == 404


def test_delete_returns_204() -> None:
    created = client.post(
        "/tasks",
        json={"title": "Delete this"},
    ).json()

    response = client.delete(f"/tasks/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""

