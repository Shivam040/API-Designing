import base64
import binascii
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status


DEFAULT_DEVELOPMENT_SECRET = "development-only-change-me"


def _secret() -> bytes:
    return os.getenv("CURSOR_SECRET", DEFAULT_DEVELOPMENT_SECRET).encode("utf-8")


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.b64decode(
        (value + padding).encode("ascii"),
        altchars=b"-_",
        validate=True,
    )


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def encode_cursor(created_at: datetime, event_id: int) -> str:
    """Create an opaque, tamper-evident cursor for the final item in a page."""
    payload = {
        "created_at": _to_utc(created_at).isoformat(),
        "id": int(event_id),
    }

    payload_bytes = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    encoded_payload = _b64encode(payload_bytes)
    signature = hmac.new(
        _secret(),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    encoded_signature = _b64encode(signature)

    # The separator is now safe: both sides are Base64URL text, whose alphabet
    # does not contain a period. We never split arbitrary binary HMAC bytes.
    return f"{encoded_payload}.{encoded_signature}"


def _invalid_cursor(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid pagination cursor",
    )


def decode_cursor(cursor: str) -> tuple[datetime, int]:
    """Validate and decode an opaque cursor into (created_at, id)."""
    try:
        parts = cursor.split(".")
        if len(parts) != 2 or not all(parts):
            raise ValueError("Malformed cursor")

        encoded_payload, encoded_signature = parts

        signature = _b64decode(encoded_signature)
        expected_signature = hmac.new(
            _secret(),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).digest()

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Cursor signature mismatch")

        payload_bytes = _b64decode(encoded_payload)
        payload: Any = json.loads(payload_bytes.decode("utf-8"))

        if not isinstance(payload, dict):
            raise TypeError("Cursor payload must be an object")
        if set(payload) != {"created_at", "id"}:
            raise ValueError("Unexpected cursor payload")
        if not isinstance(payload["created_at"], str):
            raise TypeError("Invalid created_at")
        if isinstance(payload["id"], bool) or not isinstance(payload["id"], int):
            raise TypeError("Invalid id")
        if payload["id"] < 1:
            raise ValueError("Invalid id")

        created_at = datetime.fromisoformat(payload["created_at"])
        if created_at.tzinfo is None:
            raise ValueError("Cursor timestamp must include timezone")

        return created_at.astimezone(timezone.utc), payload["id"]

    except (
        ValueError,
        TypeError,
        KeyError,
        UnicodeError,
        json.JSONDecodeError,
        binascii.Error,
    ) as exc:
        raise _invalid_cursor(exc) from exc
