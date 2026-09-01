import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone

from fastapi import HTTPException, status


CURSOR_SECRET = os.getenv(
    "CURSOR_SECRET",
    "development-only-secret",
).encode()


def _encode_base64(data: bytes) -> str:
    return (
        base64.urlsafe_b64encode(data)
        .rstrip(b"=")
        .decode()
    )


def _decode_base64(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def encode_cursor(
    created_at: datetime,
    event_id: int,
) -> str:

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    payload = {
        "created_at": created_at.astimezone(
            timezone.utc
        ).isoformat(),
        "id": event_id,
    }

    payload_bytes = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode()

    encoded_payload = _encode_base64(payload_bytes)

    signature = hmac.new(
        CURSOR_SECRET,
        encoded_payload.encode(),
        hashlib.sha256,
    ).digest()

    encoded_signature = _encode_base64(signature)

    return f"{encoded_payload}.{encoded_signature}"


def decode_cursor(
    cursor: str,
) -> tuple[datetime, int]:

    try:
        encoded_payload, encoded_signature = cursor.split(".", 1)

        signature = _decode_base64(encoded_signature)

        expected_signature = hmac.new(
            CURSOR_SECRET,
            encoded_payload.encode(),
            hashlib.sha256,
        ).digest()

        if not hmac.compare_digest(
            signature,
            expected_signature,
        ):
            raise ValueError("Invalid cursor signature")

        payload_bytes = _decode_base64(encoded_payload)
        payload = json.loads(payload_bytes)

        created_at = datetime.fromisoformat(
            payload["created_at"]
        )

        event_id = int(payload["id"])

        return created_at, event_id

    except (
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pagination cursor",
        ) from exc