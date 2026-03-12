"""
Stage 8: Report Assembly.

Assembles the final PipelineResult from all stage outputs.
Computes total token usage and AI cost estimates.
"""

from app.agents.report_generation_agent import ReportAssemblyInput, ReportGenerationAgent
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.pipeline_state import PipelineState
from app.pipeline.schemas import (
    AnomalyAnalysis,
    CampaignEvaluationResult,
    InsightGenerationResult,
    KPIResult,
    PipelineResult,
    PipelineStage,
    RecommendationResult,
    ReportRequest,
    TrendAnalysis,
    ValidationResult,
)


async def execute(
    request: ReportRequest,
    validation: ValidationResult,
    kpis: KPIResult,
    trends: TrendAnalysis,
    anomalies: AnomalyAnalysis,
    evaluation: CampaignEvaluationResult,
    insights: InsightGenerationResult,
    recommendations: RecommendationResult,
    context: PipelineContext,
    state: PipelineState,
) -> PipelineResult:
    """Assemble the final report from all stage outputs."""
    state.mark_running("report_assembly")
    context.report_progress(PipelineStage.REPORT_ASSEMBLY, 90, "Assembling report...")

    try:
        agent = ReportGenerationAgent()
        result = await agent.run(ReportAssemblyInput(
            request=request,
            validation=validation,
            kpis=kpis,
            trends=trends,
            anomalies=anomalies,
            evaluation=evaluation,
            insights=insights,
            recommendations=recommendations,
        ))
        state.mark_completed("report_assembly", result)
        return result
    except Exception as e:
        state.mark_failed("report_assembly", str(e))
        raise
