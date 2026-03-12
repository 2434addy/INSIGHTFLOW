"""
Rate limiting middleware using in-memory sliding window.

For production with multiple workers, replace the in-memory store
with Redis via `app.core.config.REDIS_URL`.

Limits are configured per-route category in config.py:
- RATE_LIMIT_AUTH: 5/15minutes (login, register)
- RATE_LIMIT_API: 100/minute (general API)
- RATE_LIMIT_REPORT_GENERATION: 10/hour (expensive operations)
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

settings = get_settings()


@dataclass
class RateLimitWindow:
    """Sliding window counter for rate limiting."""
    requests: list[float] = field(default_factory=list)

    def count_in_window(self, window_seconds: int) -> int:
        """Count requests within the sliding window, pruning expired entries."""
        cutoff = time.monotonic() - window_seconds
        self.requests = [t for t in self.requests if t > cutoff]
        return len(self.requests)

    def add_request(self) -> None:
        self.requests.append(time.monotonic())


def _parse_rate_limit(rate_str: str) -> tuple[int, int]:
    """
    Parse rate limit string like '100/minute' into (max_requests, window_seconds).

    Supported units: second, minute, hour, 15minutes.
    """
    parts = rate_str.split("/")
    max_requests = int(parts[0])
    unit = parts[1].lower()

    unit_map = {
        "second": 1,
        "minute": 60,
        "hour": 3600,
        "15minutes": 900,
    }

    window_seconds = unit_map.get(unit, 60)
    return max_requests, window_seconds


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter keyed by client IP + route category.

    Categories:
    - auth: /v1/auth/* endpoints (strict limits)
    - report: /v1/reports/*/generate (expensive AI operations)
    - api: all other /v1/* endpoints (general limit)
    - exempt: /v1/health, /docs, /openapi.json
    """

    def __init__(self, app) -> None:
        super().__init__(app)
        self._windows: dict[str, RateLimitWindow] = defaultdict(RateLimitWindow)

        # Parse configured limits
        self._limits = {
            "auth": _parse_rate_limit(settings.RATE_LIMIT_AUTH),
            "api": _parse_rate_limit(settings.RATE_LIMIT_API),
            "report": _parse_rate_limit(settings.RATE_LIMIT_REPORT_GENERATION),
        }

    def _get_category(self, path: str) -> str | None:
        """Classify a request path into a rate limit category."""
        if path.startswith("/v1/auth"):
            return "auth"
        if "/reports/" in path and path.endswith("/generate"):
            return "report"
        if path.startswith("/v1/"):
            return "api"
        return None  # Exempt

    def _get_client_key(self, request: Request) -> str:
        """Extract client identifier for rate limiting."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        category = self._get_category(request.url.path)

        if category is None:
            return await call_next(request)

        client_ip = self._get_client_key(request)
        window_key = f"{client_ip}:{category}"

        max_requests, window_seconds = self._limits[category]
        window = self._windows[window_key]

        current_count = window.count_in_window(window_seconds)

        if current_count >= max_requests:
            retry_after = window_seconds
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Rate limit exceeded. Please try again later.",
                        "details": [],
                    },
                    "meta": {
                        "retry_after": retry_after,
                    },
                },
                headers={"Retry-After": str(retry_after)},
            )

        window.add_request()

        response = await call_next(request)

        # Add rate limit headers for client awareness
        remaining = max(0, max_requests - window.count_in_window(window_seconds))
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(window_seconds)

        return response
