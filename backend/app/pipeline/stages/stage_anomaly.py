"""
Stage 4: Anomaly Detection.

Runs 4 detectors in parallel: Z-score, contextual (day-of-week),
correlation break, and missing data detection.
Runs in parallel with Stage 3 (trend detection).
"""

from app.agents.anomaly_detection_agent import AnomalyDetectionAgent, AnomalyDetectionInput
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.pipeline_state import PipelineState
from app.pipeline.schemas import AnomalyAnalysis, KPIResult, PipelineStage


async def execute(
    kpis: KPIResult,
    context: PipelineContext,
    state: PipelineState,
) -> AnomalyAnalysis:
    """Detect anomalies across all metrics."""
    state.mark_running("anomaly_detection")
    context.report_progress(PipelineStage.ANOMALY_DETECTION, 25, "Detecting anomalies...")

    try:
        agent = AnomalyDetectionAgent()
        result = await agent.run(AnomalyDetectionInput(records=kpis.records))
        state.mark_completed("anomaly_detection", result)
        return result
    except Exception as e:
        state.mark_failed("anomaly_detection", str(e))
        raise
