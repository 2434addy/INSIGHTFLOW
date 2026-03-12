"""Tests for the health check endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_returns_200(client: AsyncClient) -> None:
    """Health check should return status, version, and environment."""
    response = await client.get("/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_health_check_no_auth_required(client: AsyncClient) -> None:
    """Health check should be accessible without authentication."""
    response = await client.get("/v1/health")
    assert response.status_code == 200
