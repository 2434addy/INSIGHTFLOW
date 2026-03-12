"""
Stage 8: Report Assembly.

Assembles the final PipelineResult from all stage outputs.
Computes total token usage and AI cost estimates.
"""

from app.agents.report_generation_agent import ReportAssemblyInput, ReportGenerationAgent
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.schemas import PipelineResult
from app.pipeline.stages import BaseStage


class ReportAssemblyStage(BaseStage):
    """Assemble the final report from all stage outputs."""

    name = "report_assembly"

    async def run(self, context: PipelineContext) -> PipelineResult:
        agent = ReportGenerationAgent()
        return await agent.run(ReportAssemblyInput(
            request=context.request,
            validation=context.get_stage_output("data_validation"),
            kpis=context.get_stage_output("kpi_computation"),
            trends=context.get_stage_output("trend_detection"),
            anomalies=context.get_stage_output("anomaly_detection"),
            evaluation=context.get_stage_output("campaign_evaluation"),
            insights=context.get_stage_output("insight_generation"),
            recommendations=context.get_stage_output("recommendation_generation"),
        ))
