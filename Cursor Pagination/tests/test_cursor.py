from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.cursor import decode_cursor, encode_cursor


def test_cursor_round_trip_many_values() -> None:
    base = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

    # This specifically protects against the old binary-delimiter bug, where
    # a valid HMAC containing b'.' could make decode_cursor fail randomly.
    for event_id in range(1, 5001):
        created_at = base + timedelta(microseconds=event_id)
        cursor = encode_cursor(created_at, event_id)
        decoded_created_at, decoded_id = decode_cursor(cursor)
        assert decoded_created_at == created_at
        assert decoded_id == event_id


def test_cursor_rejects_tampering() -> None:
    cursor = encode_cursor(
        datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc),
        42,
    )
    payload, signature = cursor.split(".")
    replacement = "A" if payload[-1] != "A" else "B"
    tampered = f"{payload[:-1]}{replacement}.{signature}"

    with pytest.raises(HTTPException) as exc_info:
        decode_cursor(tampered)

    assert exc_info.value.status_code == 400
