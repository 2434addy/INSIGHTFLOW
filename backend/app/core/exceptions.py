"""
Application exception hierarchy.

All exceptions inherit from InsightFlowError.
The global exception handler in middleware converts these to RFC 7807 responses.
"""


class InsightFlowError(Exception):
    """Base exception for all InsightFlow application errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(InsightFlowError):
    """Resource not found (404)."""

    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(
            message=f"{resource} '{resource_id}' not found",
            code="NOT_FOUND",
            status_code=404,
        )


class ConflictError(InsightFlowError):
    """Resource already exists (409)."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="CONFLICT", status_code=409)


class ValidationError(InsightFlowError):
    """Input validation failed (422)."""

    def __init__(
        self,
        message: str,
        details: list[dict[str, str]] | None = None,
    ) -> None:
        self.details = details or []
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422)


class AuthenticationError(InsightFlowError):
    """Authentication failed — missing or invalid credentials (401)."""

    def __init__(self, message: str = "Invalid or missing authentication") -> None:
        super().__init__(message=message, code="UNAUTHORIZED", status_code=401)


class ForbiddenError(InsightFlowError):
    """Insufficient permissions for the requested action (403)."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message=message, code="FORBIDDEN", status_code=403)


class RateLimitError(InsightFlowError):
    """Rate limit exceeded (429)."""

    def __init__(self, retry_after: int = 60) -> None:
        self.retry_after = retry_after
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            code="RATE_LIMITED",
            status_code=429,
        )


class ExternalServiceError(InsightFlowError):
    """External API call failed (502)."""

    def __init__(self, service: str, message: str) -> None:
        super().__init__(
            message=f"External service error ({service}): {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
        )
