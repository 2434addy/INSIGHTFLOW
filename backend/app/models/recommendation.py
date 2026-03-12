"""
Recommendation model — AI-generated actionable optimization recommendations.

Produced by the Recommendation Agent, each recommendation includes an
estimated impact and implementation priority.
"""

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, JSONVariant


class Recommendation(BaseModel):
    """
    An AI-generated actionable recommendation for improving marketing performance.

    Recommendations are tied to specific insights or general report findings.
    Each includes an estimated impact, priority level, and implementation effort.
    """

    __tablename__ = "recommendations"

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
    insight_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("insights.id"),
        nullable=True,
    )
    category: Mapped[str] = mapped_column(
        String(100), nullable=False
        # 'budget', 'targeting', 'creative', 'bidding', 'scheduling'
    )
    priority: Mapped[str] = mapped_column(
        String(50), default="medium", nullable=False
        # 'critical', 'high', 'medium', 'low'
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    expected_impact: Mapped[str | None] = mapped_column(
        String(500), nullable=True  # e.g., "Estimated +15% ROAS improvement"
    )
    effort: Mapped[str] = mapped_column(
        String(50), default="medium", nullable=False
        # 'low', 'medium', 'high'
    )
    estimated_impact_value: Mapped[float | None] = mapped_column(
        Float, nullable=True  # Numeric impact estimate (e.g., percentage improvement)
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("campaigns.id"),
        nullable=True,
    )
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action_items: Mapped[dict] = mapped_column(
        JSONVariant, default=dict, nullable=False  # Structured step-by-step actions
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    report: Mapped["Report"] = relationship(  # noqa: F821
        back_populates="recommendations",
        lazy="selectin",
    )
    insight: Mapped["Insight | None"] = relationship(  # noqa: F821
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Recommendation {self.priority}: {self.title[:50]}>"
