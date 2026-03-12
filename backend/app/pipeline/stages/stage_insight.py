"""
Stage 6: Insight Generation.

Uses Claude API to generate natural language insights from the analyzed data.
Falls back to template-based insights if the AI call fails.
"""

from app.agents.insight_generation_agent import InsightGenerationAgent, InsightGenerationInput
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.schemas import InsightGenerationResult
from app.pipeline.stages import BaseStage


class InsightGenerationStage(BaseStage):
    """Generate AI-powered insights."""

    name = "insight_generation"

    async def run(self, context: PipelineContext) -> InsightGenerationResult:
        kpis = context.get_stage_output("kpi_computation")
        trends = context.get_stage_output("trend_detection")
        anomalies = context.get_stage_output("anomaly_detection")
        evaluation = context.get_stage_output("campaign_evaluation")

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
        return result
