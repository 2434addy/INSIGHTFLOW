"""
Stage 7: Recommendation Generation.

Uses Claude API to generate actionable optimization recommendations
based on insights, trends, and campaign performance data.
"""

from app.agents.recommendation_agent import RecommendationAgent, RecommendationInput
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.pipeline_state import PipelineState
from app.pipeline.schemas import (
    AnomalyAnalysis,
    CampaignEvaluationResult,
    InsightGenerationResult,
    KPIResult,
    PipelineStage,
    RecommendationResult,
    TrendAnalysis,
)


async def execute(
    kpis: KPIResult,
    trends: TrendAnalysis,
    anomalies: AnomalyAnalysis,
    evaluation: CampaignEvaluationResult,
    insights: InsightGenerationResult,
    context: PipelineContext,
    state: PipelineState,
) -> RecommendationResult:
    """Generate AI-powered recommendations."""
    state.mark_running("recommendation_generation")
    context.report_progress(
        PipelineStage.RECOMMENDATION_GENERATION, 70, "Generating recommendations..."
    )

    try:
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
        state.mark_completed("recommendation_generation", result)
        return result
    except Exception as e:
        state.mark_failed("recommendation_generation", str(e))
        raise
