"""Tests for pagination cursor utilities."""

from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.utils.pagination import decode_cursor, encode_cursor


class TestPaginationCursors:
    """Test cursor encoding/decoding."""

    def test_roundtrip(self):
        item_id = uuid4()
        cursor = encode_cursor("2024-01-15T00:00:00", item_id)
        sort_value, decoded_id = decode_cursor(cursor)
        assert sort_value == "2024-01-15T00:00:00"
        assert decoded_id == item_id

    def test_invalid_cursor_raises(self):
        with pytest.raises(ValidationError, match="Invalid pagination cursor"):
            decode_cursor("not-a-valid-cursor!!!")

    def test_empty_cursor_raises(self):
        with pytest.raises(Exception):
            decode_cursor("")

    def test_cursor_is_url_safe(self):
        cursor = encode_cursor("2024-01-15", uuid4())
        # URL-safe base64 should not contain +, /, or =
        assert "+" not in cursor
        assert "/" not in cursor
