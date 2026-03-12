"""
Campaign Evaluation Agent — Stage 5 of the analytics pipeline.

Classifies campaigns into performance tiers, assesses budget allocation,
and identifies top/bottom performers.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.base import BaseAgent
from app.pipeline.schemas import (
    CampaignEvaluationResult,
    KPIResult,
)
from app.skills.campaign_evaluation import (
    BudgetAssessor,
    PlatformComparator,
    TierClassifier,
)


@dataclass
class CampaignEvaluationInput:
    kpis: KPIResult


class CampaignEvaluationAgent(BaseAgent[CampaignEvaluationInput, CampaignEvaluationResult]):
    """Evaluates campaign performance and classifies into tiers."""

    name = "campaign_evaluation_agent"

    def __init__(self) -> None:
        self._classifier = TierClassifier()
        self._budget_assessor = BudgetAssessor()
        self._platform_comparator = PlatformComparator()

    async def execute(self, input_data: CampaignEvaluationInput) -> CampaignEvaluationResult:
        records = input_data.kpis.records
        if not records:
            return CampaignEvaluationResult()

        # Tier classification
        tiered = self._classifier.classify(records)

        # Budget assessment
        budget_assessment = self._budget_assessor.assess(tiered)

        # Platform comparison
        platform_comparison = {}
        if input_data.kpis.by_platform:
            platform_comparison = self._platform_comparator.compare(
                input_data.kpis.by_platform
            )

        # Extract top and bottom performers
        top_performers = tiered.get("star", [])[:5]
        bottom_performers = tiered.get("waster", [])[:5]

        return CampaignEvaluationResult(
            tiered_campaigns=tiered,
            budget_assessment=budget_assessment,
            top_performers=top_performers,
            bottom_performers=bottom_performers,
            platform_comparison=platform_comparison,
        )
