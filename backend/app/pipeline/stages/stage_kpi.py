"""
Stage 2: KPI Computation.

Computes derived metrics (CTR, CPC, CPA, ROAS, CVR, CPM, AOV),
aggregates by platform/campaign, and compares against the previous period.
"""

from app.agents.kpi_computation_agent import KPIComputationAgent, KPIComputationInput
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.pipeline_state import PipelineState
from app.pipeline.schemas import KPIResult, MetricRecord, PipelineStage


async def execute(
    records: list[MetricRecord],
    context: PipelineContext,
    state: PipelineState,
) -> KPIResult:
    """Compute KPIs and period comparison."""
    state.mark_running("kpi_computation")
    context.report_progress(PipelineStage.KPI_COMPUTATION, 15, "Computing KPIs...")

    try:
        agent = KPIComputationAgent()
        result = await agent.run(KPIComputationInput(
            records=records,
            date_range_start=context.date_range_start,
            date_range_end=context.date_range_end,
            comparison_period=context.comparison_period,
        ))
        state.mark_completed("kpi_computation", result)
        return result
    except Exception as e:
        state.mark_failed("kpi_computation", str(e))
        raise
