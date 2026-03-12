"""
Stage 7: Recommendation Generation.

Uses Claude API to generate actionable optimization recommendations
based on insights, trends, and campaign performance data.
"""

from app.agents.recommendation_agent import RecommendationAgent, RecommendationInput
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.schemas import RecommendationResult
from app.pipeline.stages import BaseStage


class RecommendationGenerationStage(BaseStage):
    """Generate AI-powered recommendations."""

    name = "recommendation_generation"

    async def run(self, context: PipelineContext) -> RecommendationResult:
        kpis = context.get_stage_output("kpi_computation")
        trends = context.get_stage_output("trend_detection")
        anomalies = context.get_stage_output("anomaly_detection")
        evaluation = context.get_stage_output("campaign_evaluation")
        insights = context.get_stage_output("insight_generation")

        agent = RecommendationAgent(context.anthropic_client)
        result = await agent.run(RecommendationInput(
            kpis=kpis,
            trends=trends,
            anomalies=anomalies,
            evaluation=evaluation,
            insights=insights,
            tone=context.tone,
            ai_model=context.ai_model,
        ))
        context.add_token_usage(result.tokens_used)
        return result
