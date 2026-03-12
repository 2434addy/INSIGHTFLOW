"""Tests for security headers middleware."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import create_app


@pytest.fixture
async def sec_client():
    """Client for security header tests."""
    app = create_app()

    from tests.conftest import get_test_db
    app.dependency_overrides[get_db] = get_test_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestSecurityHeaders:
    """Verify all OWASP-recommended headers are set."""

    @pytest.mark.asyncio
    async def test_x_content_type_options(self, sec_client: AsyncClient):
        response = await sec_client.get("/v1/health")
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    @pytest.mark.asyncio
    async def test_x_frame_options(self, sec_client: AsyncClient):
        response = await sec_client.get("/v1/health")
        assert response.headers["X-Frame-Options"] == "DENY"

    @pytest.mark.asyncio
    async def test_xss_protection(self, sec_client: AsyncClient):
        response = await sec_client.get("/v1/health")
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    @pytest.mark.asyncio
    async def test_referrer_policy(self, sec_client: AsyncClient):
        response = await sec_client.get("/v1/health")
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    async def test_permissions_policy(self, sec_client: AsyncClient):
        response = await sec_client.get("/v1/health")
        assert "camera=()" in response.headers["Permissions-Policy"]
        assert "microphone=()" in response.headers["Permissions-Policy"]

    @pytest.mark.asyncio
    async def test_csp_strict_on_api_routes(self, sec_client: AsyncClient):
        """API routes should have strict CSP."""
        response = await sec_client.get("/v1/health")
        assert response.headers["Content-Security-Policy"] == "default-src 'none'; frame-ancestors 'none'"

    @pytest.mark.asyncio
    async def test_cache_control_on_api_routes(self, sec_client: AsyncClient):
        """API routes should not be cached."""
        response = await sec_client.get("/v1/health")
        assert "no-store" in response.headers.get("Cache-Control", "")

    @pytest.mark.asyncio
    async def test_x_permitted_cross_domain_policies(self, sec_client: AsyncClient):
        response = await sec_client.get("/v1/health")
        assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"

    @pytest.mark.asyncio
    async def test_request_id_present(self, sec_client: AsyncClient):
        """All responses must include X-Request-ID."""
        response = await sec_client.get("/v1/health")
        assert "X-Request-ID" in response.headers
