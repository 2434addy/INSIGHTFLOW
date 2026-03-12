"""
Authentication request/response schemas.

Matches the API design from api_design.md section 2.1.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Request Schemas ────────────────────────────────────────


class RegisterRequest(BaseModel):
    """POST /v1/auth/register"""

    model_config = ConfigDict(strict=True)

    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    agency_name: str = Field(..., min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """POST /v1/auth/login"""

    model_config = ConfigDict(strict=True)

    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshTokenRequest(BaseModel):
    """POST /v1/auth/refresh — body is optional, token comes from cookie."""

    refresh_token: str | None = None


class ForgotPasswordRequest(BaseModel):
    """POST /v1/auth/forgot-password"""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """POST /v1/auth/reset-password"""

    token: str
    new_password: str = Field(..., min_length=12, max_length=128)


# ── Response Schemas ───────────────────────────────────────


class UserResponse(BaseModel):
    """User profile data in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    avatar_url: str | None
    email_verified: bool
    auth_provider: str
    created_at: datetime


class OrganizationResponse(BaseModel):
    """Organization data in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    plan: str
    created_at: datetime


class RegisterResponse(BaseModel):
    """Response after successful registration."""

    user: UserResponse
    organization: OrganizationResponse


class TokenResponse(BaseModel):
    """Response after successful login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token lifetime in seconds")


class MeResponse(BaseModel):
    """Response for GET /v1/auth/me."""

    user: UserResponse
    organizations: list[OrganizationResponse]
