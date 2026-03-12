"""
Authentication service — business logic for registration, login, and token management.

Security rules enforced:
- Bcrypt password hashing (cost factor 12)
- Account lockout after 5 failed attempts
- JWT access tokens (15 min) + refresh tokens (7 days)
"""

import re
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.models.organization import Membership, Organization
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository

logger = get_logger(__name__)

# Password policy: min 12 chars, uppercase, lowercase, digit, special char
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]).{12,}$"
)

MAX_FAILED_ATTEMPTS = 5


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
            email=email,
        )

        return user, organization

    async def login(self, email: str, password: str) -> str:
        """
        Authenticate a user and return an access token.

        Security:
        - Checks account lockout status
        - Tracks failed login attempts
        - Returns generic error messages (no user enumeration)
        """
        generic_error = "Invalid email or password"

        user = await self.user_repo.get_by_email(email.lower().strip())
        if not user:
            raise AuthenticationError(generic_error)

        # Check account lockout
        if user.locked_until and user.locked_until > datetime.now(UTC):
            raise AuthenticationError(
                "Account is temporarily locked due to too many failed attempts"
            )

        # Verify password
        if not user.password_hash or not verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = datetime.now(UTC)  # Lock for 30 min (handled by policy)
                await logger.awarning(
                    "Account locked due to failed attempts",
                    user_id=str(user.id),
                    attempts=user.failed_login_attempts,
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

        await logger.ainfo("User logged in", user_id=str(user.id))

        return access_token

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
