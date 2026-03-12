"""
Organization repository — database access for organization and membership operations.

All queries enforce soft-delete filtering and organization-scoped access.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Membership, Organization


class OrganizationRepository:
    """Data access for Organization and Membership entities."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, organization_id: UUID) -> Organization | None:
        """Fetch an organization by primary key, excluding soft-deleted."""
        result = await self.db.execute(
            select(Organization)
            .where(Organization.id == organization_id)
            .where(Organization.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Organization | None:
        """Fetch an organization by URL slug."""
        result = await self.db.execute(
            select(Organization)
            .where(Organization.slug == slug)
            .where(Organization.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_user_organizations(self, user_id: UUID) -> list[Organization]:
        """Get all organizations a user is a member of."""
        result = await self.db.execute(
            select(Organization)
            .join(Membership, Membership.organization_id == Organization.id)
            .where(Membership.user_id == user_id)
            .where(Organization.deleted_at.is_(None))
            .order_by(Organization.created_at)
        )
        return list(result.scalars().all())

    async def get_membership(
        self, user_id: UUID, organization_id: UUID
    ) -> Membership | None:
        """Get a user's membership in an organization."""
        result = await self.db.execute(
            select(Membership)
            .where(Membership.user_id == user_id)
            .where(Membership.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    async def create(self, organization: Organization) -> Organization:
        """Persist a new organization."""
        self.db.add(organization)
        await self.db.flush()
        return organization
