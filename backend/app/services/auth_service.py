"""
Authentication service — business logic for registration, login, and token management.

Security rules enforced:
- Bcrypt password hashing (cost factor 12)
- Account lockout after 5 failed attempts (30-minute window)
- JWT access tokens (15 min) + refresh tokens (7 days)
- Token rotation on refresh (old refresh token revoked)
- Generic error messages (no user enumeration)
"""

import re
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    revoke_token,
    verify_password,
)
from app.models.user import User
from app.models.organization import Membership, Organization
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository

logger = get_logger(__name__)
settings = get_settings()

# Password policy: min 12 chars, uppercase, lowercase, digit, special char
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]).{12,}$"
)


class AuthService:
    """Handles authentication and registration logic."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.org_repo = OrganizationRepository(db)

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        agency_name: str,
    ) -> tuple[User, Organization]:
        """
        Register a new user and create their organization.

        Steps:
        1. Validate password strength
        2. Check email uniqueness
        3. Create user with hashed password
        4. Create organization
        5. Create owner membership

        Returns: (user, organization)
        """
        # Validate password strength
        self._validate_password(password)

        # Check if email already exists
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ConflictError(f"An account with email '{email}' already exists")

        # Create user
        user = User(
            email=email.lower().strip(),
            password_hash=hash_password(password),
            full_name=full_name.strip(),
            auth_provider="email",
        )
        self.db.add(user)
        await self.db.flush()  # Assign user.id without committing

        # Create organization
        slug = self._generate_slug(agency_name)
        organization = Organization(
            name=agency_name.strip(),
            slug=slug,
            owner_id=user.id,
            plan="starter",
        )
        self.db.add(organization)
        await self.db.flush()

        # Create owner membership
        membership = Membership(
            user_id=user.id,
            organization_id=organization.id,
            role="owner",
        )
        self.db.add(membership)

        await logger.ainfo(
            "User registered",
            user_id=str(user.id),
            organization_id=str(organization.id),
        )

        return user, organization

    async def login(self, email: str, password: str) -> tuple[str, str]:
        """
        Authenticate a user and return access + refresh tokens.

        Security:
        - Checks account lockout status (30-minute window)
        - Tracks failed login attempts
        - Returns generic error messages (no user enumeration)

        Returns: (access_token, refresh_token)
        """
        generic_error = "Invalid email or password"

        user = await self.user_repo.get_by_email(email.lower().strip())
        if not user:
            raise AuthenticationError(generic_error)

        # Check account lockout with enforced duration
        if user.locked_until and user.locked_until > datetime.now(UTC):
            await logger.awarning(
                "Login attempt on locked account",
                user_id=str(user.id),
            )
            raise AuthenticationError(
                "Account is temporarily locked due to too many failed attempts. "
                "Try again later."
            )

        # Verify password
        if not user.password_hash or not verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                # Lock for configured duration (default 30 min)
                user.locked_until = datetime.now(UTC) + timedelta(
                    minutes=settings.ACCOUNT_LOCKOUT_MINUTES
                )
                await logger.awarning(
                    "Account locked due to failed attempts",
                    user_id=str(user.id),
                    attempts=user.failed_login_attempts,
                    locked_until=user.locked_until.isoformat(),
                )
            await self.db.flush()
            raise AuthenticationError(generic_error)

        # Successful login — reset failed attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(UTC)
        await self.db.flush()

        # Get user's first organization for token
        organizations = await self.org_repo.get_user_organizations(user.id)
        organization_id = organizations[0].id if organizations else None

        access_token = create_access_token(
            user_id=user.id,
            organization_id=organization_id,
        )
        refresh_token = create_refresh_token(user_id=user.id)

        await logger.ainfo("User logged in", user_id=str(user.id))

        return access_token, refresh_token

    async def refresh_tokens(self, user_id: UUID, old_refresh_token: str) -> tuple[str, str]:
        """
        Issue new access + refresh tokens (token rotation).

        The old refresh token is revoked to prevent replay attacks.

        Returns: (new_access_token, new_refresh_token)
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")

        # Revoke the old refresh token
        revoke_token(old_refresh_token)

        # Get user's first organization for token
        organizations = await self.org_repo.get_user_organizations(user.id)
        organization_id = organizations[0].id if organizations else None

        access_token = create_access_token(
            user_id=user.id,
            organization_id=organization_id,
        )
        refresh_token = create_refresh_token(user_id=user.id)

        await logger.ainfo("Tokens refreshed", user_id=str(user.id))

        return access_token, refresh_token

    async def logout(self, access_token: str, refresh_token: str | None = None) -> None:
        """
        Revoke access and refresh tokens on logout.
        """
        revoke_token(access_token)
        if refresh_token:
            revoke_token(refresh_token)

    async def get_user_organizations(self, user_id: UUID) -> list[Organization]:
        """Get all organizations a user is a member of."""
        return await self.org_repo.get_user_organizations(user_id)

    def _validate_password(self, password: str) -> None:
        """Enforce password policy from security_architecture.md."""
        if not PASSWORD_PATTERN.match(password):
            raise ValidationError(
                "Password must be at least 12 characters with uppercase, "
                "lowercase, number, and special character",
                details=[{"field": "password", "message": "Does not meet password policy"}],
            )

    def _generate_slug(self, name: str) -> str:
        """Generate a URL-safe slug from an agency name."""
        slug = name.lower().strip()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = slug.strip("-")
        return slug or "organization"
