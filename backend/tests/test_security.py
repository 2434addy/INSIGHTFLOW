"""
Security unit tests — JWT, password hashing, token revocation, config validation.
"""

import pytest
import jwt as pyjwt
from uuid import uuid4

from app.core.security import (
    clear_blacklist,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    revoke_token,
    verify_password,
)


@pytest.fixture(autouse=True)
def _clean_blacklist():
    """Ensure the token blacklist is clean for each test."""
    clear_blacklist()
    yield
    clear_blacklist()


class TestPasswordHashing:
    """Verify bcrypt password hashing."""

    def test_hash_and_verify(self):
        hashed = hash_password("SecureP@ssw0rd123!")
        assert verify_password("SecureP@ssw0rd123!", hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("SecureP@ssw0rd123!")
        assert not verify_password("WrongPassword!", hashed)

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("SecureP@ssw0rd123!")
        h2 = hash_password("SecureP@ssw0rd123!")
        assert h1 != h2  # Different salt each time

    def test_hash_never_contains_plaintext(self):
        password = "SecureP@ssw0rd123!"
        hashed = hash_password(password)
        assert password not in hashed


class TestJWTTokens:
    """Verify JWT token generation and verification."""

    def test_access_token_roundtrip(self):
        user_id = uuid4()
        token = create_access_token(user_id)
        payload = decode_token(token)

        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
        assert "jti" in payload  # Unique token ID for blacklisting
        assert "exp" in payload
        assert "iat" in payload

    def test_refresh_token_roundtrip(self):
        user_id = uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)

        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"
        assert "jti" in payload

    def test_access_token_with_organization(self):
        user_id = uuid4()
        org_id = uuid4()
        token = create_access_token(user_id, organization_id=org_id)
        payload = decode_token(token)

        assert payload["oid"] == str(org_id)

    def test_tokens_have_unique_jti(self):
        """Each token must have a unique ID for revocation."""
        user_id = uuid4()
        t1 = create_access_token(user_id)
        t2 = create_access_token(user_id)

        p1 = decode_token(t1)
        p2 = decode_token(t2)

        assert p1["jti"] != p2["jti"]


class TestTokenRevocation:
    """Verify token blacklist / revocation."""

    def test_revoked_token_cannot_be_decoded(self):
        user_id = uuid4()
        token = create_access_token(user_id)

        # Token works before revocation
        assert decode_token(token)["sub"] == str(user_id)

        # Revoke it
        revoke_token(token)

        # Now it raises
        with pytest.raises(pyjwt.InvalidTokenError, match="revoked"):
            decode_token(token)

    def test_revoke_refresh_token(self):
        user_id = uuid4()
        token = create_refresh_token(user_id)

        revoke_token(token)

        with pytest.raises(pyjwt.InvalidTokenError, match="revoked"):
            decode_token(token)

    def test_other_tokens_unaffected_by_revocation(self):
        user_id = uuid4()
        t1 = create_access_token(user_id)
        t2 = create_access_token(user_id)

        revoke_token(t1)

        # t2 should still work
        assert decode_token(t2)["sub"] == str(user_id)

    def test_revoke_invalid_token_is_noop(self):
        """Revoking a garbage token should not crash."""
        revoke_token("garbage.not.a.real.token")


class TestConfigValidation:
    """Verify production safety checks in Settings."""

    def test_default_secret_key_blocked_in_production(self):
        from app.core.config import Settings

        with pytest.raises(ValueError, match="SECRET_KEY.*insecure default"):
            Settings(
                ENVIRONMENT="production",
                SECRET_KEY="CHANGE-ME-IN-PRODUCTION-use-openssl-rand-hex-64",
            )

    def test_short_secret_key_blocked_in_production(self):
        from app.core.config import Settings

        with pytest.raises(ValueError, match="SECRET_KEY must be at least 64"):
            Settings(
                ENVIRONMENT="production",
                SECRET_KEY="a" * 40,  # Too short
            )

    def test_debug_blocked_in_production(self):
        from app.core.config import Settings

        with pytest.raises(ValueError, match="DEBUG must be False"):
            Settings(
                ENVIRONMENT="production",
                SECRET_KEY="a" * 128,
                DEBUG=True,
            )

    def test_wildcard_hosts_blocked_in_production(self):
        from app.core.config import Settings

        with pytest.raises(ValueError, match="ALLOWED_HOSTS"):
            Settings(
                ENVIRONMENT="production",
                SECRET_KEY="a" * 128,
                DEBUG=False,
                ALLOWED_HOSTS=["*"],
            )

    def test_development_settings_accepted(self):
        """Development mode should accept insecure defaults."""
        from app.core.config import Settings

        s = Settings(ENVIRONMENT="development")
        assert s.is_development
        # Cookie security auto-relaxed in development
        assert not s.COOKIE_SECURE
