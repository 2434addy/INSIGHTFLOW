"""
AdSet model — ad sets (Meta) / ad groups (Google) within a campaign.

Part of the ad hierarchy: Campaign → AdSet → Ad.
"""

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, JSONVariant


class AdSet(BaseModel):
    """
    An ad set or ad group within a campaign.

    Contains targeting, bidding, and scheduling configuration.
    Called 'Ad Set' in Meta Ads and 'Ad Group' in Google Ads.
    """

    __tablename__ = "ad_sets"
    __table_args__ = (
        UniqueConstraint(
            "campaign_id", "platform_ad_set_id",
            name="uq_ad_set_campaign_platform_id",
        ),
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("campaigns.id"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    platform_ad_set_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str | None] = mapped_column(
        String(50), nullable=True  # 'active', 'paused', 'completed'
    )
    targeting: Mapped[dict] = mapped_column(JSONVariant, default=dict, nullable=False)
    bid_strategy: Mapped[str | None] = mapped_column(String(100), nullable=True)
    budget_daily: Mapped[float | None] = mapped_column(nullable=True)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, default=dict, nullable=False
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship(  # noqa: F821
        back_populates="ad_sets",
        lazy="selectin",
    )
    ads: Mapped[list["Ad"]] = relationship(  # noqa: F821
        back_populates="ad_set",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<AdSet {self.name}>"
