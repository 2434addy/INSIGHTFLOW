"""
Stage 6: Insight Generation.

Uses Claude API to generate natural language insights from the analyzed data.
Falls back to template-based insights if the AI call fails.
"""

from app.agents.insight_generation_agent import InsightGenerationAgent, InsightGenerationInput
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.pipeline_state import PipelineState
from app.pipeline.schemas import (
    AnomalyAnalysis,
    CampaignEvaluationResult,
    InsightGenerationResult,
    KPIResult,
    PipelineStage,
    TrendAnalysis,
)


async def execute(
    kpis: KPIResult,
    trends: TrendAnalysis,
    anomalies: AnomalyAnalysis,
    evaluation: CampaignEvaluationResult,
    context: PipelineContext,
    state: PipelineState,
) -> InsightGenerationResult:
    """Generate AI-powered insights."""
    state.mark_running("insight_generation")
    context.report_progress(PipelineStage.INSIGHT_GENERATION, 55, "Generating insights...")

    try:
        agent = InsightGenerationAgent(context.anthropic_client)
        result = await agent.run(InsightGenerationInput(
            kpis=kpis,
            trends=trends,
            anomalies=anomalies,
            evaluation=evaluation,
            tone=context.tone,
            ai_model=context.ai_model,
        ))
        context.add_token_usage(result.tokens_used)
        state.mark_completed("insight_generation", result)
        return result
    except Exception as e:
        state.mark_failed("insight_generation", str(e))
        raise
