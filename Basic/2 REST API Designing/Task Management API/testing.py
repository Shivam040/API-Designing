from fastapi.testclient import TestClient
from .architecture import app

client = TestClient(app)


def test_create_task() -> None:
    response = client.post(
        "/tasks",
        json={
            "title": "Study FastAPI",
            "priority": "high",
        },
    )

    assert response.status_code == 201
    assert response.json()["completed"] is False
    assert response.headers["location"].startswith("/tasks/")


def test_list_tasks() -> None:
    response = client.get("/tasks")

    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)


def test_get_unknown_task() -> None:
    response = client.get("/tasks/999")

    assert response.status_code == 404


def test_put_replaces_complete_task() -> None:
    created = client.post(
        "/tasks",
        json={"title": "Old title"},
    ).json()

    response = client.put(
        f"/tasks/{created['id']}",
        json={
            "title": "New title",
            "description": None,
            "priority": "high",
            "completed": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "New title"
    assert response.json()["completed"] is True


def test_patch_preserves_unspecified_fields() -> None:
    created = client.post(
        "/tasks",
        json={
            "title": "Keep this title",
            "priority": "medium",
        },
    ).json()

    response = client.patch(
        f"/tasks/{created['id']}",
        json={"completed": True},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Keep this title"
    assert response.json()["completed"] is True


def test_empty_patch_returns_400() -> None:
    created = client.post(
        "/tasks",
        json={"title": "Task"},
    ).json()

    response = client.patch(
        f"/tasks/{created['id']}",
        json={},
    )

    assert response.status_code == 400


def test_delete_task() -> None:
    created = client.post(
        "/tasks",
        json={"title": "Delete task"},
    ).json()

    delete_response = client.delete(
        f"/tasks/{created['id']}"
    )
    get_response = client.get(
        f"/tasks/{created['id']}"
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert get_response.status_code == 404