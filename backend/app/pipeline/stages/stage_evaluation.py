"""
Stage 5: Campaign Evaluation.

Classifies campaigns into 5 tiers (star/strong/average/underperformer/waster),
assesses budget allocation efficiency, and compares across platforms.
"""

from app.agents.campaign_evaluation_agent import (
    CampaignEvaluationAgent,
    CampaignEvaluationInput,
)
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.pipeline_state import PipelineState
from app.pipeline.schemas import CampaignEvaluationResult, KPIResult, PipelineStage


async def execute(
    kpis: KPIResult,
    context: PipelineContext,
    state: PipelineState,
) -> CampaignEvaluationResult:
    """Evaluate and tier-classify all campaigns."""
    state.mark_running("campaign_evaluation")
    context.report_progress(PipelineStage.CAMPAIGN_EVALUATION, 40, "Evaluating campaigns...")

    try:
        agent = CampaignEvaluationAgent()
        result = await agent.run(CampaignEvaluationInput(kpis=kpis))
        state.mark_completed("campaign_evaluation", result)
        return result
    except Exception as e:
        state.mark_failed("campaign_evaluation", str(e))
        raise
