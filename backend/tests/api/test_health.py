"""Tests for the health check endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_returns_200(client: AsyncClient) -> None:
    """Health check should return status and service name."""
    response = await client.get("/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "InsightFlow API"


@pytest.mark.asyncio
async def test_health_check_no_auth_required(client: AsyncClient) -> None:
    """Health check should be accessible without authentication."""
    response = await client.get("/v1/health")
    assert response.status_code == 200
