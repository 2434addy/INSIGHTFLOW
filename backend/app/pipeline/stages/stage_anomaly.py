"""
Stage 4: Anomaly Detection.

Runs 4 detectors in parallel: Z-score, contextual (day-of-week),
correlation break, and missing data detection.
Runs in parallel with Stage 3 (trend detection).
"""

from app.agents.anomaly_detection_agent import AnomalyDetectionAgent, AnomalyDetectionInput
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.schemas import AnomalyAnalysis
from app.pipeline.stages import BaseStage


class AnomalyDetectionStage(BaseStage):
    """Detect anomalies across all metrics."""

    name = "anomaly_detection"

    async def run(self, context: PipelineContext) -> AnomalyAnalysis:
        kpis = context.get_stage_output("kpi_computation")
        agent = AnomalyDetectionAgent()
        return await agent.run(AnomalyDetectionInput(records=kpis.records))
