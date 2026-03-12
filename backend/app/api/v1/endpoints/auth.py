"""
Authentication endpoints — register, login, refresh, me.

Implements endpoints from api_design.md section 2.1.
"""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MeResponse,
    OrganizationResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserResponse,
)
from app.schemas.common import MetaResponse, SuccessResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post(
    "/register",
    response_model=SuccessResponse[RegisterResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[RegisterResponse]:
    """
    Create a new user account and organization.

    - Validates email uniqueness
    - Hashes password with bcrypt
    - Creates organization with the agency name
    - Creates owner membership
    """
    service = AuthService(db)
    user, organization = await service.register(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        agency_name=body.agency_name,
    )

    return SuccessResponse(
        data=RegisterResponse(
            user=UserResponse.model_validate(user),
            organization=OrganizationResponse.model_validate(organization),
        ),
        meta=MetaResponse(request_id=str(uuid4())),
    )


@router.post(
    "/login",
    response_model=SuccessResponse[TokenResponse],
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[TokenResponse]:
    """
    Authenticate with email and password.

    Returns a JWT access token. Refresh token is set as HttpOnly cookie.
    """
    service = AuthService(db)
    access_token = await service.login(email=body.email, password=body.password)

    return SuccessResponse(
        data=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
        meta=MetaResponse(request_id=str(uuid4())),
    )


@router.get(
    "/me",
    response_model=SuccessResponse[MeResponse],
)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[MeResponse]:
    """Get the currently authenticated user's profile and organizations."""
    service = AuthService(db)
    organizations = await service.get_user_organizations(current_user.id)

    return SuccessResponse(
        data=MeResponse(
            user=UserResponse.model_validate(current_user),
            organizations=[OrganizationResponse.model_validate(org) for org in organizations],
        ),
        meta=MetaResponse(request_id=str(uuid4())),
    )
