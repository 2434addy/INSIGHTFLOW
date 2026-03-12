"""
Pipeline state machine — tracks stage completion and enables resumability.

If a pipeline run fails mid-execution, state allows restarting from the
last successful stage rather than re-running the entire pipeline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageState:
    """Execution state for a single pipeline stage."""
    status: StageStatus = StageStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int = 0
    error: str | None = None
    output: Any = None


@dataclass
class PipelineState:
    """
    Tracks the execution state of all pipeline stages.

    Enables:
    - Progress monitoring (which stages are done / in-progress)
    - Resumability (skip completed stages on retry)
    - Audit trail (timing and errors per stage)
    """

    report_id: UUID
    stages: dict[str, StageState] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Default stage ordering (matches DAG)
    STAGE_ORDER = [
        "data_validation",
        "kpi_computation",
        "trend_detection",
        "anomaly_detection",
        "campaign_evaluation",
        "insight_generation",
        "recommendation_generation",
        "report_assembly",
    ]

    def __post_init__(self) -> None:
        """Initialize all stages as pending."""
        for stage_name in self.STAGE_ORDER:
            if stage_name not in self.stages:
                self.stages[stage_name] = StageState()

    def mark_running(self, stage_name: str) -> None:
        """Mark a stage as currently executing."""
        state = self.stages[stage_name]
        state.status = StageStatus.RUNNING
        state.started_at = datetime.now(UTC)
        logger.debug("Pipeline %s: stage %s → RUNNING", self.report_id, stage_name)

    def mark_completed(self, stage_name: str, output: Any = None) -> None:
        """Mark a stage as successfully completed."""
        state = self.stages[stage_name]
        state.status = StageStatus.COMPLETED
        state.completed_at = datetime.now(UTC)
        state.output = output
        if state.started_at:
            delta = state.completed_at - state.started_at
            state.duration_ms = int(delta.total_seconds() * 1000)
        logger.debug(
            "Pipeline %s: stage %s → COMPLETED (%dms)",
            self.report_id, stage_name, state.duration_ms,
        )

    def mark_failed(self, stage_name: str, error: str) -> None:
        """Mark a stage as failed."""
        state = self.stages[stage_name]
        state.status = StageStatus.FAILED
        state.completed_at = datetime.now(UTC)
        state.error = error
        if state.started_at:
            delta = state.completed_at - state.started_at
            state.duration_ms = int(delta.total_seconds() * 1000)
        logger.error(
            "Pipeline %s: stage %s → FAILED: %s",
            self.report_id, stage_name, error,
        )

    def is_completed(self, stage_name: str) -> bool:
        """Check if a stage has already completed (for resumability)."""
        return self.stages[stage_name].status == StageStatus.COMPLETED

    def get_output(self, stage_name: str) -> Any:
        """Get the output of a completed stage."""
        return self.stages[stage_name].output

    @property
    def is_finished(self) -> bool:
        """True if all stages are completed or skipped."""
        return all(
            s.status in (StageStatus.COMPLETED, StageStatus.SKIPPED)
            for s in self.stages.values()
        )

    @property
    def has_failures(self) -> bool:
        """True if any stage has failed."""
        return any(s.status == StageStatus.FAILED for s in self.stages.values())

    def summary(self) -> dict[str, str]:
        """Return a summary of stage statuses for logging/API responses."""
        return {name: state.status.value for name, state in self.stages.items()}

    def timing_report(self) -> dict[str, int]:
        """Return duration in ms for each completed stage."""
        return {
            name: state.duration_ms
            for name, state in self.stages.items()
            if state.status == StageStatus.COMPLETED
        }
