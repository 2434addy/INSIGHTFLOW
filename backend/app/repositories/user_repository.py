"""
User repository — database access layer for user operations.

All queries filter by deleted_at IS NULL for soft-delete support.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Data access for User entities."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Fetch a user by primary key, excluding soft-deleted."""
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .where(User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email address, excluding soft-deleted."""
        result = await self.db.execute(
            select(User)
            .where(User.email == email.lower())
            .where(User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_provider(self, provider: str, provider_id: str) -> User | None:
        """Fetch a user by OAuth provider identity."""
        result = await self.db.execute(
            select(User)
            .where(User.auth_provider == provider)
            .where(User.provider_id == provider_id)
            .where(User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Persist a new user."""
        self.db.add(user)
        await self.db.flush()
        return user
