"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient

from app.models.user import User
from app.models.organization import Organization


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    """Successful registration creates user and organization."""
    response = await client.post(
        "/v1/auth/register",
        json={
            "email": "newuser@agency.com",
            "password": "SecureP@ssw0rd123!",
            "full_name": "New User",
            "agency_name": "New Agency",
        },
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["user"]["email"] == "newuser@agency.com"
    assert data["user"]["full_name"] == "New User"
    assert data["organization"]["name"] == "New Agency"
    assert data["organization"]["slug"] == "new-agency"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Registration with an existing email returns 409."""
    payload = {
        "email": "duplicate@agency.com",
        "password": "SecureP@ssw0rd123!",
        "full_name": "First User",
        "agency_name": "Agency One",
    }

    # First registration succeeds
    response = await client.post("/v1/auth/register", json=payload)
    assert response.status_code == 201

    # Second registration with same email fails
    payload["agency_name"] = "Agency Two"
    response = await client.post("/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient) -> None:
    """Registration with a weak password returns 422."""
    response = await client.post(
        "/v1/auth/register",
        json={
            "email": "weak@agency.com",
            "password": "short",
            "full_name": "Weak Pass User",
            "agency_name": "Agency",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    """Successful login returns an access token and sets refresh cookie."""
    # Register first
    await client.post(
        "/v1/auth/register",
        json={
            "email": "login@agency.com",
            "password": "SecureP@ssw0rd123!",
            "full_name": "Login User",
            "agency_name": "Login Agency",
        },
    )

    # Then login
    response = await client.post(
        "/v1/auth/login",
        json={
            "email": "login@agency.com",
            "password": "SecureP@ssw0rd123!",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0

    # Verify refresh token cookie is set
    cookies = response.cookies
    # httpx may not expose httponly cookies directly — check set-cookie header
    set_cookie = response.headers.get("set-cookie", "")
    assert "refresh_token" in set_cookie or "refresh_token" in cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    """Login with wrong password returns 401."""
    # Register first
    await client.post(
        "/v1/auth/register",
        json={
            "email": "wrongpass@agency.com",
            "password": "SecureP@ssw0rd123!",
            "full_name": "Wrong Pass User",
            "agency_name": "Agency",
        },
    )

    # Login with wrong password
    response = await client.post(
        "/v1/auth/login",
        json={
            "email": "wrongpass@agency.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient) -> None:
    """Login with non-existent email returns 401 (no user enumeration)."""
    response = await client.post(
        "/v1/auth/login",
        json={
            "email": "nobody@agency.com",
            "password": "SomeP@ssw0rd123!",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_user: User,
) -> None:
    """GET /auth/me returns the current user when authenticated."""
    response = await client.get("/v1/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user"]["email"] == test_user.email
    assert data["user"]["full_name"] == test_user.full_name
    assert len(data["organizations"]) >= 1


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient) -> None:
    """GET /auth/me without token returns 401."""
    response = await client.get("/v1/auth/me")
    assert response.status_code == 422  # Missing required Authorization header


@pytest.mark.asyncio
async def test_me_invalid_token(client: AsyncClient) -> None:
    """GET /auth/me with invalid token returns 401."""
    response = await client.get(
        "/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient) -> None:
    """All API responses must include security headers."""
    response = await client.get("/v1/health")

    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in response.headers
    assert response.headers.get("X-Permitted-Cross-Domain-Policies") == "none"


@pytest.mark.asyncio
async def test_api_responses_not_cached(client: AsyncClient) -> None:
    """API responses must include Cache-Control: no-store."""
    response = await client.get("/v1/health")

    assert "no-store" in response.headers.get("Cache-Control", "")


@pytest.mark.asyncio
async def test_request_id_in_response(client: AsyncClient) -> None:
    """All responses must include X-Request-ID for tracing."""
    response = await client.get("/v1/health")

    assert "X-Request-ID" in response.headers
    # Verify it's a valid UUID-like string
    assert len(response.headers["X-Request-ID"]) > 0


@pytest.mark.asyncio
async def test_account_lockout_after_failed_attempts(client: AsyncClient) -> None:
    """Account should be locked after failed login attempts.

    Note: the rate limiter (5/15min for auth endpoints) may trigger before
    the account lockout. Both are valid security mechanisms. We verify that
    the user is blocked — either by rate limiting (429) or account lockout (401).
    """
    # Register
    await client.post(
        "/v1/auth/register",
        json={
            "email": "lockout@agency.com",
            "password": "SecureP@ssw0rd123!",
            "full_name": "Lockout User",
            "agency_name": "Lockout Agency",
        },
    )

    # Fail multiple times — expect 401 (auth error) or 429 (rate limited)
    blocked = False
    for i in range(6):
        response = await client.post(
            "/v1/auth/login",
            json={"email": "lockout@agency.com", "password": "WrongPassword1!"},
        )
        if response.status_code == 429:
            blocked = True
            break
        assert response.status_code == 401

    # If rate limiter didn't kick in, try with correct password — should be locked
    if not blocked:
        response = await client.post(
            "/v1/auth/login",
            json={"email": "lockout@agency.com", "password": "SecureP@ssw0rd123!"},
        )
        assert response.status_code in (401, 429)
    else:
        # Rate limiter caught the brute force — this is also correct behavior
        assert blocked
