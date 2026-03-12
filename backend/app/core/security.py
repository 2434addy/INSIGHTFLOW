"""
Security utilities: JWT tokens, password hashing, and token revocation.

Implements:
- JWT access/refresh token generation and verification
- Bcrypt password hashing (cost factor configurable, default 12)
- Token blacklist for revocation on logout
- Refresh token rotation (new refresh token on every refresh)
"""

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
import jwt

from app.core.config import get_settings

settings = get_settings()

# ── In-memory token blacklist ─────────────────────────────────
# For production with multiple workers, replace with Redis:
#   SETNX f"blacklist:{jti}" 1 EX <remaining_ttl>
_token_blacklist: set[str] = set()


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(
    user_id: UUID,
    organization_id: UUID | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token (short-lived, 15 min default).

    Claims:
        sub: user ID
        oid: organization ID (optional)
        exp: expiration timestamp
        iat: issued-at timestamp
        jti: unique token ID (for blacklist)
        type: "access"
    """
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    payload: dict[str, str | float] = {
        "sub": str(user_id),
        "exp": expire.timestamp(),
        "iat": now.timestamp(),
        "jti": secrets.token_hex(16),
        "type": "access",
    }

    if organization_id:
        payload["oid"] = str(organization_id)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    user_id: UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT refresh token (long-lived, 7 days default).

    Stored in HttpOnly cookie — never exposed to JavaScript.
    """
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))

    payload: dict[str, str | float] = {
        "sub": str(user_id),
        "exp": expire.timestamp(),
        "iat": now.timestamp(),
        "jti": secrets.token_hex(16),
        "type": "refresh",
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.

    Also checks the token blacklist for revoked tokens.

    Raises:
        jwt.ExpiredSignatureError: Token has expired
        jwt.InvalidTokenError: Token is malformed, signature invalid, or revoked
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )

    # Check if token has been revoked (blacklisted)
    jti = payload.get("jti")
    if jti and jti in _token_blacklist:
        raise jwt.InvalidTokenError("Token has been revoked")

    return payload


def revoke_token(token: str) -> None:
    """
    Add a token to the blacklist so it can no longer be used.

    Called on logout to invalidate both access and refresh tokens.
    For production: use Redis with TTL matching the token's remaining lifetime.
    """
    try:
        # Decode without verification to get the jti even if expired
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False},
        )
        jti = payload.get("jti")
        if jti:
            _token_blacklist.add(jti)
    except jwt.InvalidTokenError:
        pass  # If the token is completely invalid, nothing to revoke


def clear_blacklist() -> None:
    """Clear the token blacklist. Used in tests only."""
    _token_blacklist.clear()
