"""
Metrics model — time-series performance data from marketing platforms.

Stores daily/hourly metrics with both core (unified) and platform-specific fields.
Designed for partitioning by date in PostgreSQL.
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, JSONVariant


class Metrics(BaseModel):
    """
    Performance metrics for a campaign on a given date.

    Core metrics are unified across all platforms. Platform-specific
    extended metrics are stored in the platform_data JSON column.
    """

    __tablename__ = "metrics"
    __table_args__ = (
        UniqueConstraint(
            "campaign_id", "date", "granularity",
            name="uq_metrics_campaign_date_granularity",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("campaigns.id"),
        nullable=True,
        index=True,
    )
    ad_set_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("ad_sets.id"),
        nullable=True,
    )
    ad_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("ads.id"),
        nullable=True,
    )
    connection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("data_source_connections.id"),
        nullable=False,
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    granularity: Mapped[str] = mapped_column(
        String(20), default="daily", nullable=False  # 'hourly', 'daily'
    )

    # Core metrics (unified across platforms)
    impressions: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    spend: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    conversions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversion_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )

    # Derived metrics (computed on insert/update)
    ctr: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    cpc: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    cpa: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    roas: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)

    # Platform-specific extended metrics
    platform_data: Mapped[dict] = mapped_column(JSONVariant, default=dict, nullable=False)

    # Relationships
    campaign: Mapped["Campaign | None"] = relationship(  # noqa: F821
        back_populates="metrics",
        lazy="selectin",
    )

    def compute_derived_metrics(self) -> None:
        """Compute CTR, CPC, CPA, and ROAS from core metrics."""
        if self.impressions > 0:
            self.ctr = Decimal(self.clicks) / Decimal(self.impressions)
        if self.clicks > 0:
            self.cpc = self.spend / Decimal(self.clicks)
        if self.conversions > 0:
            self.cpa = self.spend / Decimal(self.conversions)
        if self.spend > 0:
            self.roas = self.conversion_value / self.spend

    def __repr__(self) -> str:
        return f"<Metrics campaign={self.campaign_id} date={self.date}>"
