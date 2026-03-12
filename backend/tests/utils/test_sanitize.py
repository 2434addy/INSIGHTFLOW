"""Tests for sanitization utilities."""

from app.utils.sanitize import sanitize_dict, sanitize_headers, sanitize_url


class TestSanitizeDict:
    """Test dictionary sanitization."""

    def test_redacts_password(self):
        result = sanitize_dict({"email": "user@test.com", "password": "secret123"})
        assert result["email"] == "user@test.com"
        assert result["password"] == "***REDACTED***"

    def test_redacts_nested(self):
        result = sanitize_dict({"user": {"token": "abc123", "name": "Test"}})
        assert result["user"]["token"] == "***REDACTED***"
        assert result["user"]["name"] == "Test"

    def test_redacts_in_list(self):
        result = sanitize_dict({
            "items": [{"secret": "x"}, {"name": "y"}]
        })
        assert result["items"][0]["secret"] == "***REDACTED***"
        assert result["items"][1]["name"] == "y"

    def test_handles_max_depth(self):
        deep = {"a": {"b": {"c": {"d": {"e": {"f": {"g": "deep"}}}}}}}
        result = sanitize_dict(deep)
        # Should not crash, just truncate at depth 5
        assert "__truncated__" in str(result)

    def test_case_insensitive_keys(self):
        result = sanitize_dict({"API_KEY": "secret", "api_key": "secret"})
        assert result["api_key"] == "***REDACTED***"


class TestSanitizeUrl:
    """Test URL credential redaction."""

    def test_redacts_credentials(self):
        url = "postgresql+asyncpg://user:pass@localhost:5432/db"
        result = sanitize_url(url)
        assert "user" not in result
        assert "pass" not in result
        assert "***:***@localhost:5432/db" in result

    def test_no_credentials(self):
        url = "redis://localhost:6379/0"
        result = sanitize_url(url)
        assert result == url


class TestSanitizeHeaders:
    """Test HTTP header sanitization."""

    def test_redacts_authorization(self):
        result = sanitize_headers({
            "Authorization": "Bearer xyz",
            "Content-Type": "application/json",
        })
        assert result["Authorization"] == "***REDACTED***"
        assert result["Content-Type"] == "application/json"

    def test_redacts_cookie(self):
        result = sanitize_headers({"Cookie": "session=abc"})
        assert result["Cookie"] == "***REDACTED***"
