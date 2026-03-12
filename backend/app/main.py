"""
InsightFlow API — Application entry point.

Creates and configures the FastAPI application with:
- CORS middleware (origins from config, never wildcard)
- Security headers middleware (OWASP)
- Rate limiting middleware
- Request context middleware (distributed tracing)
- Request body size limit
- Global error handlers (RFC 7807 responses)
- Health check and versioned API routers
- Startup/shutdown lifecycle hooks
- security.txt at /.well-known/security.txt
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
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
from app.middleware.request_size import RequestSizeLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifecycle manager.

    Startup:
    - Initialize structured logging
    - Validate configuration safety
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

    if settings.is_development and settings.SECRET_KEY == "CHANGE-ME-IN-PRODUCTION-use-openssl-rand-hex-64":
        await logger.awarning(
            "Using default SECRET_KEY — acceptable for development only"
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
        # Swagger UI disabled in production — no schema exposure
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # ── Middleware (order matters — outermost first) ───

    # CORS — allow only configured frontend origins, never wildcard
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Organization-ID"],
        max_age=86400,
    )

    # Security headers (OWASP)
    app.add_middleware(SecurityHeadersMiddleware)

    # Rate limiting per IP + route category
    app.add_middleware(RateLimiterMiddleware)

    # Request body size limit (default 1 MB)
    app.add_middleware(RequestSizeLimitMiddleware)

    # Request context binding (distributed tracing via X-Request-ID)
    app.add_middleware(RequestContextMiddleware)

    # ── Exception Handlers ────────────────────────────
    app.add_exception_handler(InsightFlowError, insightflow_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    # ── Routers ───────────────────────────────────────
    app.include_router(api_router)

    # ── Well-known endpoints ──────────────────────────

    @app.get("/.well-known/security.txt", include_in_schema=False)
    async def security_txt() -> PlainTextResponse:
        """RFC 9116 security.txt — responsible disclosure contact."""
        return PlainTextResponse(
            "Contact: security@insightflow.app\n"
            "Preferred-Languages: en\n"
            "Canonical: https://insightflow.app/.well-known/security.txt\n"
            "Policy: https://insightflow.app/security-policy\n"
        )

    return app


# Application instance used by uvicorn
app = create_app()
