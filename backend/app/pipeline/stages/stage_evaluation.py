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
from app.pipeline.schemas import CampaignEvaluationResult
from app.pipeline.stages import BaseStage


class CampaignEvaluationStage(BaseStage):
    """Evaluate and tier-classify all campaigns."""

    name = "campaign_evaluation"

    async def run(self, context: PipelineContext) -> CampaignEvaluationResult:
        kpis = context.get_stage_output("kpi_computation")
        agent = CampaignEvaluationAgent()
        return await agent.run(CampaignEvaluationInput(kpis=kpis))
