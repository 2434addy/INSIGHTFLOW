"""
Stage 2: KPI Computation.

Computes derived metrics (CTR, CPC, CPA, ROAS, CVR, CPM, AOV),
aggregates by platform/campaign, and compares against the previous period.
"""

from app.agents.kpi_computation_agent import KPIComputationAgent, KPIComputationInput
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.schemas import KPIResult
from app.pipeline.stages import BaseStage


class KPIComputationStage(BaseStage):
    """Compute KPIs and period comparison."""

    name = "kpi_computation"

    async def run(self, context: PipelineContext) -> KPIResult:
        agent = KPIComputationAgent()
        return await agent.run(KPIComputationInput(
            records=context.records,
            date_range_start=context.date_range_start,
            date_range_end=context.date_range_end,
            comparison_period=context.comparison_period,
        ))
