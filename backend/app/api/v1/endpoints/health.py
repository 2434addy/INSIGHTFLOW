"""
Health check endpoint.

Used by load balancers, container orchestrators, and monitoring tools
to verify the API is running and responsive.
"""

from fastapi import APIRouter

from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return application health status."""
    return HealthResponse()
