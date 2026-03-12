"""
Stage 3: Trend Detection.

Classifies metric trends using OLS regression, computes moving averages,
and analyzes budget pacing. Runs in parallel with Stage 4 (anomaly detection).
"""

from app.agents.trend_detection_agent import TrendDetectionAgent, TrendDetectionInput
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.pipeline_state import PipelineState
from app.pipeline.schemas import KPIResult, PipelineStage, TrendAnalysis


async def execute(
    kpis: KPIResult,
    context: PipelineContext,
    state: PipelineState,
) -> TrendAnalysis:
    """Detect trends across all metrics."""
    state.mark_running("trend_detection")
    context.report_progress(PipelineStage.TREND_DETECTION, 25, "Detecting trends...")

    try:
        agent = TrendDetectionAgent()
        result = await agent.run(TrendDetectionInput(records=kpis.records))
        state.mark_completed("trend_detection", result)
        return result
    except Exception as e:
        state.mark_failed("trend_detection", str(e))
        raise
