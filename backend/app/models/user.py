"""
User model — authentication and profile data.

Maps to the 'users' table defined in database_schema.md.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, SoftDeleteMixin


class User(BaseModel, SoftDeleteMixin):
    """User account for InsightFlow."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True  # NULL for OAuth-only users
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email_verified: Mapped[bool] = mapped_column(default=False, nullable=False)

    # OAuth fields
    auth_provider: Mapped[str] = mapped_column(
        String(50), default="email", nullable=False
    )
    provider_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Security fields
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    memberships: Mapped[list["Membership"]] = relationship(  # noqa: F821
        back_populates="user",
        lazy="selectin",
    )
    owned_organizations: Mapped[list["Organization"]] = relationship(  # noqa: F821
        back_populates="owner",
        foreign_keys="Organization.owner_id",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
