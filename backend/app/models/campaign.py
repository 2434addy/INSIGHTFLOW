"""
Campaign model — synced marketing campaigns from connected platforms.

Part of the ad hierarchy: Campaign → AdSet → Ad.
"""

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, JSONVariant


class Campaign(BaseModel):
    """
    A marketing campaign synced from an external platform.

    Campaigns are the top level of the ad hierarchy. They contain
    ad sets (or ad groups) which contain individual ads.
    """

    __tablename__ = "campaigns"
    __table_args__ = (
        UniqueConstraint(
            "connection_id", "platform_campaign_id",
            name="uq_campaign_connection_platform_id",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    connection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("data_source_connections.id"),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(
        String(50), nullable=False  # 'meta_ads', 'google_ads', 'ga4', 'shopify'
    )
    platform_campaign_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str | None] = mapped_column(
        String(50), nullable=True  # 'active', 'paused', 'completed', 'archived'
    )
    campaign_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True  # 'search', 'display', 'video', 'shopping'
    )
    objective: Mapped[str | None] = mapped_column(
        String(100), nullable=True  # 'conversions', 'traffic', 'awareness'
    )
    budget_daily: Mapped[float | None] = mapped_column(nullable=True)
    budget_lifetime: Mapped[float | None] = mapped_column(nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, default=dict, nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        back_populates="campaigns",
        lazy="selectin",
    )
    connection: Mapped["DataSourceConnection"] = relationship(  # noqa: F821
        back_populates="campaigns",
        lazy="selectin",
    )
    ad_sets: Mapped[list["AdSet"]] = relationship(  # noqa: F821
        back_populates="campaign",
        lazy="noload",
    )
    metrics: Mapped[list["Metrics"]] = relationship(  # noqa: F821
        back_populates="campaign",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Campaign {self.name} ({self.platform})>"
