"""
InsightFlow API — Application entry point.

Creates and configures the FastAPI application with:
- CORS middleware
- Request context middleware (distributed tracing)
- Global error handlers (RFC 7807 responses)
- Health check and versioned API routers
- Startup/shutdown lifecycle hooks
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import close_db
from app.core.exceptions import InsightFlowError
from app.core.logging import get_logger, setup_logging
from app.middleware.error_handler import (
    insightflow_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifecycle manager.

    Startup:
    - Initialize structured logging
    - Log application start

    Shutdown:
    - Close database connection pool
    """
    # ── Startup ────────────────────────────────────────
    setup_logging()
    logger = get_logger("app.main")
    await logger.ainfo(
        "InsightFlow API starting",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
    )

    yield

    # ── Shutdown ───────────────────────────────────────
    await logger.ainfo("InsightFlow API shutting down")
    await close_db()


def create_app() -> FastAPI:
    """
    Application factory.

    Creates a configured FastAPI instance. Used by uvicorn and tests.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered marketing analytics and report generation platform",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # ── Middleware (order matters — outermost first) ───
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Organization-ID"],
        max_age=86400,
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimiterMiddleware)
    app.add_middleware(RequestContextMiddleware)

    # ── Exception Handlers ────────────────────────────
    app.add_exception_handler(InsightFlowError, insightflow_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    # ── Routers ───────────────────────────────────────
    app.include_router(api_router)

    return app


# Application instance used by uvicorn
app = create_app()
