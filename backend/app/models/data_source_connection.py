"""
DataSourceConnection model — platform integrations (Meta Ads, Google Ads, GA4, Shopify).

Stores OAuth credentials (encrypted), sync state, and platform-specific metadata.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, JSONVariant


class DataSourceConnection(BaseModel):
    """
    A connection to an external marketing platform.

    OAuth tokens are stored encrypted (AES-256-GCM) with a wrapped DEK.
    """

    __tablename__ = "data_source_connections"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "platform", "account_id",
            name="uq_connection_org_platform_account",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(
        String(50), nullable=False  # 'meta_ads', 'google_ads', 'ga4', 'shopify'
    )
    account_id: Mapped[str] = mapped_column(
        String(255), nullable=False  # Platform-specific account ID
    )
    account_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Encrypted OAuth credentials
    encrypted_access_token: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    encrypted_refresh_token: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    wrapped_dek: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scopes: Mapped[list | None] = mapped_column(JSONVariant, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="active", nullable=False  # 'active', 'expired', 'revoked', 'error'
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sync_frequency: Mapped[str] = mapped_column(
        String(50), default="daily", nullable=False  # 'hourly', 'daily', 'weekly'
    )
    config: Mapped[dict] = mapped_column(JSONVariant, default=dict, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        back_populates="connections",
        lazy="selectin",
    )
    campaigns: Mapped[list["Campaign"]] = relationship(  # noqa: F821
        back_populates="connection",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<DataSourceConnection {self.platform}:{self.account_id}>"
