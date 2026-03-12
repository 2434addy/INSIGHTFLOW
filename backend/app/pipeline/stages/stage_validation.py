"""
Stage 1: Data Validation.

Validates raw metric records for completeness, type correctness,
and business rule compliance before entering the analytics pipeline.
"""

from app.agents.data_validation_agent import DataValidationAgent, DataValidationInput
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.pipeline_state import PipelineState
from app.pipeline.schemas import MetricRecord, PipelineStage, ValidationResult


async def execute(
    records: list[MetricRecord],
    context: PipelineContext,
    state: PipelineState,
) -> ValidationResult:
    """Run data validation and return the validation result."""
    state.mark_running("data_validation")
    context.report_progress(PipelineStage.DATA_VALIDATION, 5, "Validating data...")

    try:
        agent = DataValidationAgent()
        result = await agent.run(DataValidationInput(records=records))
        state.mark_completed("data_validation", result)
        return result
    except Exception as e:
        state.mark_failed("data_validation", str(e))
        raise
