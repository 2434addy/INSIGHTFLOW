"""
Security utilities: JWT tokens, password hashing, and encryption.

Implements:
- JWT access/refresh token generation and verification
- Bcrypt password hashing
- Secure random token generation
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
import jwt

from app.core.config import get_settings

settings = get_settings()


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
    Create a JWT access token.

    Claims:
        sub: user ID
        oid: organization ID (optional)
        exp: expiration timestamp
        iat: issued-at timestamp
        type: "access"
    """
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    payload: dict[str, str | float] = {
        "sub": str(user_id),
        "exp": expire.timestamp(),
        "iat": now.timestamp(),
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
    Create a JWT refresh token.

    Longer-lived than access tokens. Stored in HttpOnly cookie.
    """
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))

    payload: dict[str, str | float] = {
        "sub": str(user_id),
        "exp": expire.timestamp(),
        "iat": now.timestamp(),
        "type": "refresh",
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.

    Raises:
        jwt.ExpiredSignatureError: Token has expired
        jwt.InvalidTokenError: Token is malformed or signature is invalid
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
