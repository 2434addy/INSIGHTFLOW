"""
Recommendation Agent — Stage 7 of the analytics pipeline.

Generates actionable optimization recommendations using Claude API,
based on analysis data and generated insights.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from app.agents.base import BaseAgent
from app.pipeline.schemas import (
    AnomalyAnalysis,
    CampaignEvaluationResult,
    GeneratedRecommendation,
    InsightGenerationResult,
    KPIResult,
    RecommendationCategory,
    RecommendationResult,
    TrendAnalysis,
)
from app.skills.insight_summarization import InsightParser, InsightPromptBuilder

logger = logging.getLogger(__name__)


@dataclass
class RecommendationInput:
    kpis: KPIResult
    trends: TrendAnalysis
    anomalies: AnomalyAnalysis
    evaluation: CampaignEvaluationResult
    insights: InsightGenerationResult
    tone: str = "executive"
    ai_model: str = "claude-sonnet-4-6"


class RecommendationAgent(BaseAgent[RecommendationInput, RecommendationResult]):
    """Generates AI-powered optimization recommendations."""

    name = "recommendation_agent"
    max_retries = 2

    def __init__(self, anthropic_client=None) -> None:
        self._client = anthropic_client
        self._prompt_builder = InsightPromptBuilder()
        self._parser = InsightParser()

    async def execute(self, input_data: RecommendationInput) -> RecommendationResult:
        if self._client is None:
            logger.warning("No Anthropic client, using template recommendations")
            return await self.fallback(input_data, None)

        system_prompt = self._prompt_builder.build_system_prompt(input_data.tone)
        data_context = self._prompt_builder.build_data_context(
            kpis=input_data.kpis,
            trends=input_data.trends,
            anomalies=input_data.anomalies,
            evaluation=input_data.evaluation,
        )
        insights_json = json.dumps(
            [i.model_dump() for i in input_data.insights.insights],
            default=str,
        )
        rec_prompt = self._prompt_builder.build_recommendation_prompt(
            data_context, insights_json
        )

        response = await self._client.messages.create(
            model=input_data.ai_model,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": rec_prompt}],
        )
        raw_text = response.content[0].text
        total_tokens = response.usage.input_tokens + response.usage.output_tokens

        raw_recs = self._parser.parse_recommendations(raw_text)
        recommendations = self._parse_recs(raw_recs)

        return RecommendationResult(
            recommendations=recommendations,
            ai_model=input_data.ai_model,
            tokens_used=total_tokens,
        )

    async def fallback(
        self, input_data: RecommendationInput, error: Exception | None
    ) -> RecommendationResult:
        """Generate template-based recommendations."""
        logger.warning("Using template fallback for recommendations: %s", error)
        recs = self._generate_template_recs(input_data)
        return RecommendationResult(
            recommendations=recs,
            ai_model="template_fallback",
            tokens_used=0,
        )

    @staticmethod
    def _parse_recs(raw_recs: list[dict]) -> list[GeneratedRecommendation]:
        results: list[GeneratedRecommendation] = []
        for item in raw_recs:
            if not all(k in item for k in ["title", "description"]):
                continue
            try:
                category = RecommendationCategory(item.get("category", "budget"))
            except ValueError:
                category = RecommendationCategory.BUDGET

            results.append(GeneratedRecommendation(
                category=category,
                priority=item.get("priority", "medium"),
                title=item["title"],
                description=item["description"],
                expected_impact=item.get("expected_impact", ""),
                estimated_impact_value=item.get("estimated_impact_value"),
                effort=item.get("effort", "medium"),
                action_items=item.get("action_items", []),
            ))
        return results

    @staticmethod
    def _generate_template_recs(
        input_data: RecommendationInput,
    ) -> list[GeneratedRecommendation]:
        """Produce basic recommendations from structured data."""
        recs: list[GeneratedRecommendation] = []

        # Budget reallocation if waster campaigns exist
        eval_result = input_data.evaluation
        if eval_result.bottom_performers:
            waster_spend = sum(c.spend for c in eval_result.bottom_performers)
            recs.append(GeneratedRecommendation(
                category=RecommendationCategory.BUDGET,
                priority="high",
                title="Reallocate budget from underperforming campaigns",
                description=(
                    f"${waster_spend:,.2f} is allocated to underperforming campaigns. "
                    "Consider pausing or reducing spend on these and redirecting "
                    "budget to top performers."
                ),
                expected_impact="Improved overall ROAS",
                effort="low",
                action_items=[
                    "Review underperforming campaigns",
                    "Pause campaigns with ROAS below 1.0x",
                    "Increase budget for star campaigns",
                ],
            ))

        # Trend-based recommendation
        for trend in input_data.trends.trends:
            if trend.direction.value in ("decreasing", "declining") and trend.metric == "conversions":
                recs.append(GeneratedRecommendation(
                    category=RecommendationCategory.TARGETING,
                    priority="high",
                    title="Address declining conversion trend",
                    description=(
                        f"Conversions are {trend.direction.value} with a strength of "
                        f"{trend.strength}. Review targeting, creative, and landing pages."
                    ),
                    expected_impact="Stabilize conversion performance",
                    effort="medium",
                    action_items=[
                        "Audit audience targeting settings",
                        "Refresh ad creative",
                        "Check landing page performance",
                    ],
                ))

        if not recs:
            recs.append(GeneratedRecommendation(
                category=RecommendationCategory.BUDGET,
                priority="medium",
                title="Continue monitoring campaign performance",
                description="Current performance is stable. Continue monitoring and optimize iteratively.",
                expected_impact="Maintain performance levels",
                effort="low",
                action_items=["Review weekly performance reports"],
            ))

        return recs
