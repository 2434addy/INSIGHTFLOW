"""
Shared schemas used across all API endpoints.

Implements the standard response envelope from api_design.md:
- data: The response payload
- meta: Request metadata (request_id, timestamp)
- error: Error details (on failure)
"""

from datetime import UTC, datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class MetaResponse(BaseModel):
    """Metadata included in every API response."""

    request_id: str = Field(description="Unique request identifier for tracing")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Server timestamp of the response",
    )


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response envelope."""

    data: T
    meta: MetaResponse


class ErrorDetail(BaseModel):
    """A single validation error detail."""

    field: str | None = None
    message: str


class ErrorBody(BaseModel):
    """Error payload in error responses."""

    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Standard error response envelope (RFC 7807 inspired)."""

    error: ErrorBody
    meta: MetaResponse


class PaginationParams(BaseModel):
    """Query parameters for cursor-based pagination."""

    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=20, ge=1, le=100, description="Number of items to return")
    cursor: str | None = Field(default=None, description="Pagination cursor")


class PaginationMeta(BaseModel):
    """Pagination metadata in list responses."""

    cursor: str | None = Field(description="Next page cursor, null if no more pages")
    has_more: bool
    total: int | None = Field(default=None, description="Total count (when available)")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list response."""

    data: list[T]
    pagination: PaginationMeta
    meta: MetaResponse


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    environment: str
