"""
Request body size limit middleware.

Rejects requests with Content-Length exceeding the configured maximum
(default 1 MB) to prevent resource exhaustion attacks.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

settings = get_settings()


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose body exceeds MAX_REQUEST_BODY_BYTES."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        content_length = request.headers.get("content-length")

        if content_length and int(content_length) > settings.MAX_REQUEST_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={
                    "error": {
                        "code": "PAYLOAD_TOO_LARGE",
                        "message": (
                            f"Request body exceeds the "
                            f"{settings.MAX_REQUEST_BODY_BYTES // 1024}KB limit"
                        ),
                        "details": [],
                    },
                    "meta": {},
                },
            )

        return await call_next(request)
