"""
Input sanitization and safe logging utilities.

Ensures secrets are never exposed in logs or error messages.
"""

import re
from typing import Any


# Patterns that indicate sensitive data
_SENSITIVE_KEYS = frozenset({
    "password", "password_hash", "secret", "secret_key", "token",
    "access_token", "refresh_token", "api_key", "authorization",
    "cookie", "session", "credit_card", "ssn", "private_key",
    "client_secret", "encrypted_access_token", "encrypted_refresh_token",
})

_REDACTED = "***REDACTED***"


def sanitize_dict(data: dict[str, Any], depth: int = 0) -> dict[str, Any]:
    """
    Recursively redact sensitive fields from a dictionary.

    Used before logging request/response payloads to prevent secret exposure.
    Max depth of 5 to prevent infinite recursion on circular references.
    """
    if depth > 5:
        return {"__truncated__": True}

    sanitized = {}
    for key, value in data.items():
        if key.lower() in _SENSITIVE_KEYS:
            sanitized[key] = _REDACTED
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, depth + 1)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_dict(item, depth + 1) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


def sanitize_url(url: str) -> str:
    """Remove credentials from database/service URLs before logging."""
    return re.sub(
        r"://[^@]+@",
        "://***:***@",
        url,
    )


def sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    """Redact sensitive HTTP headers."""
    sensitive_headers = {"authorization", "cookie", "x-api-key", "x-csrf-token"}
    return {
        k: (_REDACTED if k.lower() in sensitive_headers else v)
        for k, v in headers.items()
    }
