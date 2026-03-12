"""
Organization and Membership models — multi-tenant organization layer.

Each agency gets one organization. Users access organizations via memberships with roles.
"""

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, JSONVariant, SoftDeleteMixin


class Organization(BaseModel, SoftDeleteMixin):
    """
    Organization represents a single agency tenant.

    All client data, integrations, and reports are scoped to an organization.
    """

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
    )
    plan: Mapped[str] = mapped_column(
        String(50), default="starter", nullable=False
    )
    settings: Mapped[dict] = mapped_column(JSONVariant, default=dict, nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship(  # noqa: F821
        back_populates="owned_organizations",
        foreign_keys=[owner_id],
        lazy="selectin",
    )
    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="organization",
        lazy="selectin",
    )
    connections: Mapped[list["DataSourceConnection"]] = relationship(  # noqa: F821
        back_populates="organization",
        lazy="noload",
    )
    campaigns: Mapped[list["Campaign"]] = relationship(  # noqa: F821
        back_populates="organization",
        lazy="noload",
    )
    reports: Mapped[list["Report"]] = relationship(  # noqa: F821
        back_populates="organization",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Organization {self.slug}>"


class Membership(BaseModel):
    """
    Junction between User and Organization with role assignment.

    Roles: owner, admin, member, viewer
    """

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_membership_user_organization"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(50), default="member", nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(  # noqa: F821
        back_populates="memberships",
        lazy="selectin",
    )
    organization: Mapped["Organization"] = relationship(
        back_populates="memberships",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Membership user={self.user_id} org={self.organization_id} role={self.role}>"
