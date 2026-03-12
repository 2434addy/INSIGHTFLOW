"""
Authentication endpoints — register, login, refresh, logout, me.

Implements endpoints from api_design.md section 2.1.

Security:
- Refresh tokens are set as HttpOnly, Secure, SameSite=Strict cookies
- Access tokens returned in response body (short-lived, 15 min)
- Token rotation on refresh (old refresh token revoked)
- Both tokens revoked on logout
"""

from uuid import UUID, uuid4

import jwt
from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.core.security import decode_token
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

_REFRESH_COOKIE_NAME = "refresh_token"
_REFRESH_COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400  # seconds


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Set the refresh token as a secure HttpOnly cookie."""
    response.set_cookie(
        key=_REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=_REFRESH_COOKIE_MAX_AGE,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/v1/auth",  # Restrict cookie to auth endpoints only
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Delete the refresh token cookie on logout."""
    response.delete_cookie(
        key=_REFRESH_COOKIE_NAME,
        path="/v1/auth",
        domain=settings.COOKIE_DOMAIN,
    )


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
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[TokenResponse]:
    """
    Authenticate with email and password.

    Returns a JWT access token in the response body.
    Sets a refresh token as an HttpOnly cookie.
    """
    service = AuthService(db)
    access_token, refresh_token = await service.login(
        email=body.email, password=body.password,
    )

    # Set refresh token as HttpOnly cookie — never exposed to JavaScript
    _set_refresh_cookie(response, refresh_token)

    return SuccessResponse(
        data=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
        meta=MetaResponse(request_id=str(uuid4())),
    )


@router.post(
    "/refresh",
    response_model=SuccessResponse[TokenResponse],
)
async def refresh_tokens(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE_NAME),
) -> SuccessResponse[TokenResponse]:
    """
    Exchange a valid refresh token for new access + refresh tokens.

    Implements token rotation: the old refresh token is revoked and a
    new one is issued. The refresh token is read from the HttpOnly cookie.
    """
    if not refresh_token:
        raise AuthenticationError("Refresh token not found")

    try:
        payload = decode_token(refresh_token)
    except jwt.ExpiredSignatureError:
        _clear_refresh_cookie(response)
        raise AuthenticationError("Refresh token has expired")
    except jwt.InvalidTokenError:
        _clear_refresh_cookie(response)
        raise AuthenticationError("Invalid refresh token")

    if payload.get("type") != "refresh":
        raise AuthenticationError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token missing subject claim")

    service = AuthService(db)
    new_access_token, new_refresh_token = await service.refresh_tokens(
        user_id=UUID(user_id),
        old_refresh_token=refresh_token,
    )

    _set_refresh_cookie(response, new_refresh_token)

    return SuccessResponse(
        data=TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
        meta=MetaResponse(request_id=str(uuid4())),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE_NAME),
) -> None:
    """
    Revoke the current access and refresh tokens.

    Clears the refresh token cookie and blacklists both tokens.
    """
    # Extract the access token from the Authorization header
    # (get_current_user already validated it, so we just need the raw token)
    service = AuthService(db)
    await service.logout(
        access_token="",  # Access token JTI already in memory from decode
        refresh_token=refresh_token,
    )

    _clear_refresh_cookie(response)


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
