"""
Global exception handler middleware.

Catches all InsightFlowError subclasses and converts them to
standard JSON error responses matching the API design spec.
"""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import InsightFlowError, RateLimitError
from app.core.logging import get_logger

logger = get_logger(__name__)


async def insightflow_error_handler(
    request: Request, exc: InsightFlowError
) -> JSONResponse:
    """Handle all InsightFlowError subclasses."""
    request_id = request.headers.get("X-Request-ID", str(uuid4()))

    await logger.awarning(
        "Application error",
        error_code=exc.code,
        error_message=exc.message,
        status_code=exc.status_code,
        request_id=request_id,
        path=str(request.url.path),
        method=request.method,
    )

    headers = {}
    if isinstance(exc, RateLimitError):
        headers["Retry-After"] = str(exc.retry_after)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": getattr(exc, "details", []),
            },
            "meta": {
                "request_id": request_id,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        },
        headers=headers,
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic / FastAPI validation errors."""
    request_id = request.headers.get("X-Request-ID", str(uuid4()))

    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        details.append({
            "field": field or None,
            "message": error["msg"],
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": details,
            },
            "meta": {
                "request_id": request_id,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        },
    )


async def unhandled_error_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all for unhandled exceptions. Logs full error, returns generic message."""
    request_id = request.headers.get("X-Request-ID", str(uuid4()))

    await logger.aerror(
        "Unhandled exception",
        error_type=type(exc).__name__,
        error_message=str(exc),
        request_id=request_id,
        path=str(request.url.path),
        method=request.method,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": [],
            },
            "meta": {
                "request_id": request_id,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        },
    )
