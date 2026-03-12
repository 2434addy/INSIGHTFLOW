"""Tests for rate limiting middleware."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import create_app


@pytest_asyncio.fixture
async def rate_limited_client():
    """Client for rate limiting tests."""
    app = create_app()

    # Override DB for tests
    from tests.conftest import get_test_db
    app.dependency_overrides[get_db] = get_test_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestRateLimiter:
    """Rate limiting middleware tests."""

    @pytest.mark.asyncio
    async def test_health_not_rate_limited(self, rate_limited_client: AsyncClient):
        """Health endpoint should be exempt from rate limiting."""
        for _ in range(20):
            response = await rate_limited_client.get("/v1/health")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(self, rate_limited_client: AsyncClient):
        """Rate-limited endpoints should include X-RateLimit-* headers."""
        response = await rate_limited_client.post(
            "/v1/auth/login",
            json={"email": "test@test.com", "password": "x"},
        )
        # Even if login fails (401/422), headers should be present
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
