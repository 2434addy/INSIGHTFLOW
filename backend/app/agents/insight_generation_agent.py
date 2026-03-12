"""
Insight Generation Agent — Stage 6 of the analytics pipeline.

Uses Claude API to generate AI-powered insights from structured analysis data.
Falls back to templates when AI generation fails.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from app.agents.base import BaseAgent
from app.pipeline.schemas import (
    AnomalyAnalysis,
    CampaignEvaluationResult,
    InsightGenerationResult,
    KPIResult,
    TrendAnalysis,
)
from app.skills.insight_summarization import (
    InsightParser,
    InsightPromptBuilder,
    TemplateFallback,
)

logger = logging.getLogger(__name__)


@dataclass
class InsightGenerationInput:
    kpis: KPIResult
    trends: TrendAnalysis
    anomalies: AnomalyAnalysis
    evaluation: CampaignEvaluationResult
    tone: str = "executive"
    ai_model: str = "claude-sonnet-4-6"


class InsightGenerationAgent(BaseAgent[InsightGenerationInput, InsightGenerationResult]):
    """Generates AI-powered insights using Claude API."""

    name = "insight_generation_agent"
    max_retries = 2  # AI calls can be flaky

    def __init__(self, anthropic_client=None) -> None:
        self._client = anthropic_client
        self._prompt_builder = InsightPromptBuilder()
        self._parser = InsightParser()
        self._fallback = TemplateFallback()

    async def execute(self, input_data: InsightGenerationInput) -> InsightGenerationResult:
        # Build prompts
        system_prompt = self._prompt_builder.build_system_prompt(input_data.tone)
        data_context = self._prompt_builder.build_data_context(
            kpis=input_data.kpis,
            trends=input_data.trends,
            anomalies=input_data.anomalies,
            evaluation=input_data.evaluation,
        )
        insight_prompt = self._prompt_builder.build_insight_prompt(data_context)

        # Call Claude API
        total_tokens = 0
        if self._client is None:
            logger.warning("No Anthropic client configured, using template fallback")
            return await self.fallback(input_data, None)

        # Generate insights
        response = await self._client.messages.create(
            model=input_data.ai_model,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": insight_prompt}],
        )
        insight_text = response.content[0].text
        total_tokens += response.usage.input_tokens + response.usage.output_tokens

        insights = self._parser.parse_insights(insight_text)

        # Generate executive summary
        summary_prompt = self._prompt_builder.build_executive_summary_prompt(
            data_context,
            json.dumps([i.model_dump() for i in insights[:3]], default=str),
        )
        summary_response = await self._client.messages.create(
            model=input_data.ai_model,
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": summary_prompt}],
        )
        executive_summary = summary_response.content[0].text
        total_tokens += summary_response.usage.input_tokens + summary_response.usage.output_tokens

        return InsightGenerationResult(
            insights=insights,
            executive_summary=executive_summary,
            ai_model=input_data.ai_model,
            tokens_used=total_tokens,
        )

    async def fallback(
        self, input_data: InsightGenerationInput, error: Exception | None
    ) -> InsightGenerationResult:
        """Use template-based insights when AI fails."""
        logger.warning("Using template fallback for insights: %s", error)
        insights = self._fallback.generate_fallback_insights(
            input_data.kpis,
            input_data.evaluation,
        )
        return InsightGenerationResult(
            insights=insights,
            executive_summary="Report insights generated using template analysis.",
            ai_model="template_fallback",
            tokens_used=0,
        )
