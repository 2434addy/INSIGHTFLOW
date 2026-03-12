"""
Stage 1: Data Validation.

Validates raw metric records for completeness, type correctness,
and business rule compliance before entering the analytics pipeline.
"""

from app.agents.data_validation_agent import DataValidationAgent, DataValidationInput
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.schemas import ValidationResult
from app.pipeline.stages import BaseStage


class DataValidationStage(BaseStage):
    """Validate incoming metric records."""

    name = "data_validation"

    async def run(self, context: PipelineContext) -> ValidationResult:
        agent = DataValidationAgent()
        return await agent.run(DataValidationInput(records=context.records))
