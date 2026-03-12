"""
Shared FastAPI dependencies for authentication, authorization, and pagination.

These are injected into route handlers via Depends().
"""

from uuid import UUID

import jwt
from fastapi import Depends, Header, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, ForbiddenError
from app.core.security import decode_token
from app.models.user import User
from app.models.organization import Membership, Organization
from app.schemas.common import PaginationParams

settings = get_settings()


async def get_pagination(
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> PaginationParams:
    """Parse and validate pagination query parameters."""
    return PaginationParams(limit=limit, cursor=cursor)


async def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate the JWT access token from the Authorization header.
    Returns the authenticated User or raises AuthenticationError.
    """
    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Authorization header must use Bearer scheme")

    token = authorization[7:]  # Strip "Bearer " prefix

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Access token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid access token")

    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token missing subject claim")

    result = await db.execute(
        select(User)
        .where(User.id == UUID(user_id))
        .where(User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("User not found")

    return user


async def get_current_organization(
    x_organization_id: str = Header(..., alias="X-Organization-ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    """
    Resolve the organization from X-Organization-ID header and verify the
    current user is a member. All tenant-scoped endpoints use this.
    """
    try:
        organization_id = UUID(x_organization_id)
    except ValueError:
        raise AuthenticationError("Invalid organization ID format")

    # Verify user is a member of this organization
    result = await db.execute(
        select(Membership)
        .where(Membership.user_id == current_user.id)
        .where(Membership.organization_id == organization_id)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise ForbiddenError("You are not a member of this organization")

    # Fetch the organization
    result = await db.execute(
        select(Organization)
        .where(Organization.id == organization_id)
        .where(Organization.deleted_at.is_(None))
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise ForbiddenError("Organization not found or has been deleted")

    return organization


def require_role(*allowed_roles: str):
    """
    Dependency factory that checks the user's role in the current organization.

    Usage:
        @router.delete("/{id}", dependencies=[Depends(require_role("owner", "admin"))])
    """

    async def _check_role(
        current_user: User = Depends(get_current_user),
        organization: Organization = Depends(get_current_organization),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        result = await db.execute(
            select(Membership)
            .where(Membership.user_id == current_user.id)
            .where(Membership.organization_id == organization.id)
        )
        membership = result.scalar_one_or_none()

        if not membership or membership.role not in allowed_roles:
            raise ForbiddenError(
                f"This action requires one of these roles: {', '.join(allowed_roles)}"
            )

    return _check_role
