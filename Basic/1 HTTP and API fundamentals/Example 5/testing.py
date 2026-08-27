from fastapi.testclient import TestClient
from .Architecture import app

client = TestClient(app)

def test_path_query_and_body_are_processed_correctly() -> None:
    response = client.patch(
        "/employees/1",
        params={"send_notification": True},
        json={"department":"Analytics"},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["employee"]["id"] == 1
    assert body["employee"]["department"] == "Analytics"
    assert body["notification_requested"] is True


def test_unspecified_fields_remain_unchanged() -> None:
    response = client.patch(
        "/employees/1",
        json={"active": False},
    )

    assert response.status_code == 200
    assert response.json()["employee"]["name"] == "Neha"
    assert response.json()["employee"]["active"] == False


def test_invalid_path_parameter_returns_422() -> None:
    response = client.patch(
        "/employees/1",
        json={},
    )

    assert response.status_code == 400

