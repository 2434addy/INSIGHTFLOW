"""
Security headers middleware.

Adds OWASP-recommended security headers to all responses.

CSP policy:
- API routes: strict ``default-src 'none'`` blocks everything.
- /docs and /redoc (development only): relaxed CSP allows Swagger UI
  resources from cdn.jsdelivr.net and fastapi.tiangolo.com.
  These paths are disabled in production via FastAPI(docs_url=None).
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings

settings = get_settings()

# Swagger UI needs inline styles/scripts and CDN resources.
# Only used in development — these paths return 404 in production.
_DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' https://fastapi.tiangolo.com data:; "
    "font-src 'self' https://cdn.jsdelivr.net; "
    "connect-src 'self'; "
    "frame-ancestors 'none'"
)

# Strict CSP for all API routes — blocks everything.
_API_CSP = "default-src 'none'; frame-ancestors 'none'"

# Paths that need the relaxed CSP (only served in development).
_DOCS_PATHS = frozenset({"/docs", "/redoc", "/openapi.json"})


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy — don't leak URLs to third parties
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy — disable unused browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # Prevent Adobe cross-domain policy loading
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # HSTS in production — force HTTPS for 1 year with preload
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Cache-Control — prevent caching of API responses with sensitive data
        if request.url.path.startswith("/v1/auth") or request.url.path.startswith("/v1/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        # Content-Security-Policy: relaxed for docs in dev, strict everywhere else
        if settings.is_development and request.url.path in _DOCS_PATHS:
            response.headers["Content-Security-Policy"] = _DOCS_CSP
        else:
            response.headers["Content-Security-Policy"] = _API_CSP

        return response
