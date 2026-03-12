"""
Insight model — AI-generated analytical insights from report data.

Insights are produced by the Insight Generation Agent and validated
by the Validation Agent before inclusion in a report.
"""

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, JSONVariant


class Insight(BaseModel):
    """
    An AI-generated insight derived from marketing performance data.

    Each insight represents a key finding, trend, or observation that
    the AI pipeline has identified from the metrics data. Insights are
    validated against source data before being included in reports.
    """

    __tablename__ = "insights"

    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(100), nullable=False
        # 'performance', 'trend', 'anomaly', 'comparison', 'attribution'
    )
    severity: Mapped[str] = mapped_column(
        String(50), default="info", nullable=False
        # 'critical', 'warning', 'info', 'positive'
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_data: Mapped[dict] = mapped_column(
        JSONVariant, default=dict, nullable=False
    )
    confidence_score: Mapped[float | None] = mapped_column(
        Float, nullable=True  # 0.0 to 1.0, set by Validation Agent
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("campaigns.id"),
        nullable=True,
    )
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    report: Mapped["Report"] = relationship(  # noqa: F821
        back_populates="insights",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Insight {self.category}: {self.title[:50]}>"
