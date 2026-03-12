"""
Ad model — individual ads within an ad set.

Part of the ad hierarchy: Campaign → AdSet → Ad.
"""

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, JSONVariant


class Ad(BaseModel):
    """
    An individual ad creative within an ad set.

    Contains the ad creative details, format, and platform-specific metadata.
    """

    __tablename__ = "ads"
    __table_args__ = (
        UniqueConstraint(
            "ad_set_id", "platform_ad_id",
            name="uq_ad_adset_platform_id",
        ),
    )

    ad_set_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("ad_sets.id"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    platform_ad_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str | None] = mapped_column(
        String(50), nullable=True  # 'active', 'paused', 'disapproved'
    )
    ad_format: Mapped[str | None] = mapped_column(
        String(100), nullable=True  # 'image', 'video', 'carousel', 'text'
    )
    headline: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body_text: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    destination_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    preview_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONVariant, default=dict, nullable=False
    )

    # Relationships
    ad_set: Mapped["AdSet"] = relationship(  # noqa: F821
        back_populates="ads",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Ad {self.name}>"
