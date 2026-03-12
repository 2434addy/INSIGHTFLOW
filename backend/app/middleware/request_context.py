"""
Request context middleware.

Binds request-scoped context (request_id, path, method) to structlog
so all log entries within a request automatically include tracing info.
"""

from uuid import uuid4

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    1. Extracts or generates X-Request-ID for distributed tracing
    2. Binds request context to structlog for automatic inclusion in logs
    3. Adds X-Request-ID to response headers
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Extract or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid4()))

        # Bind context to structlog for this request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        # Process the request
        response = await call_next(request)

        # Add request ID to response headers for client-side tracing
        response.headers["X-Request-ID"] = request_id

        return response
