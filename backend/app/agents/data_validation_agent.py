"""
Data Validation Agent — Stage 1 of the analytics pipeline.

Validates raw metric records for completeness, correctness, and consistency
before passing them to downstream stages.
"""

from __future__ import annotations

import logging

from app.agents.base import BaseAgent
from app.pipeline.schemas import MetricRecord, ValidationResult
from app.skills.data_quality_validation import RawDataValidator

logger = logging.getLogger(__name__)


class DataValidationInput:
    def __init__(self, records: list[MetricRecord]):
        self.records = records


class DataValidationAgent(BaseAgent[DataValidationInput, ValidationResult]):
    """Validates raw metric records and reports issues."""

    name = "data_validation_agent"
    max_retries = 0  # Validation is deterministic — no point retrying

    def __init__(self) -> None:
        self._validator = RawDataValidator()

    async def execute(self, input_data: DataValidationInput) -> ValidationResult:
        result = self._validator.validate(input_data.records)

        if result.errors:
            logger.warning(
                "Data validation found %d errors in %d records (%.1f%% error rate)",
                len(result.errors),
                result.total_records,
                result.error_rate * 100,
            )
        if result.warnings:
            logger.info(
                "Data validation found %d warnings",
                len(result.warnings),
            )

        return result
