from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Event


def insert_events(db: Session, count: int = 7) -> None:
    base = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    statuses = ("pending", "completed", "failed")
    db.add_all(
        [
            Event(
                status=statuses[i % 3],
                created_at=base + timedelta(minutes=i),
            )
            for i in range(count)
        ]
    )
    db.commit()


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_event(client: TestClient) -> None:
    response = client.post("/events", json={"status": "pending"})
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["status"] == "pending"
    assert body["created_at"]


def test_invalid_status_is_rejected(client: TestClient) -> None:
    response = client.post("/events", json={"status": "unknown"})
    assert response.status_code == 422


def test_cursor_pagination_returns_every_row_once(
    client: TestClient,
    db: Session,
) -> None:
    insert_events(db, count=7)

    seen_ids: list[int] = []
    cursor: str | None = None

    while True:
        params: dict[str, str | int] = {"limit": 3}
        if cursor is not None:
            params["cursor"] = cursor

        response = client.get("/events", params=params)
        assert response.status_code == 200
        body = response.json()

        seen_ids.extend(item["id"] for item in body["data"])

        if not body["pagination"]["has_more"]:
            assert body["pagination"]["next_cursor"] is None
            break

        cursor = body["pagination"]["next_cursor"]
        assert cursor

    assert seen_ids == [7, 6, 5, 4, 3, 2, 1]
    assert len(seen_ids) == len(set(seen_ids)) == 7


def test_same_timestamp_uses_id_as_tie_breaker(
    client: TestClient,
    db: Session,
) -> None:
    same_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    db.add_all(
        [Event(status="pending", created_at=same_time) for _ in range(5)]
    )
    db.commit()

    first = client.get("/events", params={"limit": 2}).json()
    assert [item["id"] for item in first["data"]] == [5, 4]

    second = client.get(
        "/events",
        params={"limit": 2, "cursor": first["pagination"]["next_cursor"]},
    ).json()
    assert [item["id"] for item in second["data"]] == [3, 2]

    third = client.get(
        "/events",
        params={"limit": 2, "cursor": second["pagination"]["next_cursor"]},
    ).json()
    assert [item["id"] for item in third["data"]] == [1]
    assert third["pagination"]["has_more"] is False
    assert third["pagination"]["next_cursor"] is None


def test_filter_works_with_cursor_pagination(
    client: TestClient,
    db: Session,
) -> None:
    insert_events(db, count=10)

    first = client.get(
        "/events",
        params={"status": "pending", "limit": 2},
    )
    assert first.status_code == 200
    first_body = first.json()
    assert all(item["status"] == "pending" for item in first_body["data"])
    assert first_body["pagination"]["has_more"] is True

    second = client.get(
        "/events",
        params={
            "status": "pending",
            "limit": 2,
            "cursor": first_body["pagination"]["next_cursor"],
        },
    )
    assert second.status_code == 200
    second_body = second.json()
    assert all(item["status"] == "pending" for item in second_body["data"])

    ids = [item["id"] for item in first_body["data"] + second_body["data"]]
    assert ids == [10, 7, 4, 1]
    assert len(ids) == len(set(ids))


def test_invalid_cursor_returns_400(client: TestClient) -> None:
    response = client.get("/events", params={"cursor": "not-a-valid-cursor"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid pagination cursor"}


def test_limit_validation(client: TestClient) -> None:
    assert client.get("/events", params={"limit": 0}).status_code == 422
    assert client.get("/events", params={"limit": 101}).status_code == 422
