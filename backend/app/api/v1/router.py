"""
V1 API router — aggregates all module routers under the /v1 prefix.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, health

api_router = APIRouter(prefix="/v1")

# Health check — no auth required
api_router.include_router(health.router)

# Authentication
api_router.include_router(auth.router)
