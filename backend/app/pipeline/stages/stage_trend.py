"""
Stage 3: Trend Detection.

Classifies metric trends using OLS regression, computes moving averages,
and analyzes budget pacing. Runs in parallel with Stage 4 (anomaly detection).
"""

from app.agents.trend_detection_agent import TrendDetectionAgent, TrendDetectionInput
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.schemas import TrendAnalysis
from app.pipeline.stages import BaseStage


class TrendDetectionStage(BaseStage):
    """Detect trends across all metrics."""

    name = "trend_detection"

    async def run(self, context: PipelineContext) -> TrendAnalysis:
        kpis = context.get_stage_output("kpi_computation")
        agent = TrendDetectionAgent()
        return await agent.run(TrendDetectionInput(records=kpis.records))
