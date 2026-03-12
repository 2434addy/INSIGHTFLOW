"""
Report Generation Agent — Stage 8 (final) of the analytics pipeline.

Assembles all pipeline outputs into a final report and persists it
to the database. Also triggers async PDF generation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.agents.base import BaseAgent
from app.pipeline.schemas import (
    AnomalyAnalysis,
    CampaignEvaluationResult,
    InsightGenerationResult,
    KPIResult,
    PipelineResult,
    RecommendationResult,
    ReportRequest,
    TrendAnalysis,
    ValidationResult,
)

logger = logging.getLogger(__name__)


@dataclass
class ReportAssemblyInput:
    request: ReportRequest
    validation: ValidationResult
    kpis: KPIResult
    trends: TrendAnalysis
    anomalies: AnomalyAnalysis
    evaluation: CampaignEvaluationResult
    insights: InsightGenerationResult
    recommendations: RecommendationResult


class ReportGenerationAgent(BaseAgent[ReportAssemblyInput, PipelineResult]):
    """Assembles all pipeline outputs into a final report."""

    name = "report_generation_agent"

    async def execute(self, input_data: ReportAssemblyInput) -> PipelineResult:
        total_tokens = (
            input_data.insights.tokens_used
            + input_data.recommendations.tokens_used
        )

        # Estimate AI cost
        ai_cost = self._estimate_cost(
            total_tokens,
            input_data.request.ai_model,
        )

        result = PipelineResult(
            report_id=input_data.request.report_id,
            validation=input_data.validation,
            kpis=input_data.kpis,
            trends=input_data.trends,
            anomalies=input_data.anomalies,
            campaign_evaluation=input_data.evaluation,
            insights=input_data.insights,
            recommendations=input_data.recommendations,
            total_tokens_used=total_tokens,
            total_ai_cost=ai_cost,
        )

        logger.info(
            "Report %s assembled: %d insights, %d recommendations, %d tokens ($%.4f)",
            input_data.request.report_id,
            len(input_data.insights.insights),
            len(input_data.recommendations.recommendations),
            total_tokens,
            ai_cost,
        )

        return result

    @staticmethod
    def _estimate_cost(tokens: int, model: str) -> float:
        """Estimate AI API cost based on token usage."""
        # Approximate costs per 1K tokens (blended input+output)
        costs_per_1k = {
            "claude-sonnet-4-6": 0.009,
            "claude-opus-4-6": 0.045,
        }
        rate = costs_per_1k.get(model, 0.009)
        return (tokens / 1000) * rate
