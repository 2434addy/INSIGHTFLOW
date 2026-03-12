"""
Cursor-based pagination utilities.

Encodes/decodes opaque cursors for stable pagination across requests.
Uses base64-encoded JSON with (sort_value, id) for deterministic ordering.
"""

import base64
import json
from uuid import UUID

from app.core.exceptions import ValidationError


def encode_cursor(sort_value: str, item_id: UUID) -> str:
    """Encode a pagination cursor from sort value and item ID."""
    payload = json.dumps({"s": sort_value, "id": str(item_id)})
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_cursor(cursor: str) -> tuple[str, UUID]:
    """
    Decode a pagination cursor.

    Returns (sort_value, item_id).
    Raises ValidationError if cursor is malformed.
    """
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor))
        return payload["s"], UUID(payload["id"])
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise ValidationError("Invalid pagination cursor") from e
