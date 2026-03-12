"""
Pipeline execution context.

Carries shared state, configuration, and dependencies through all pipeline
stages. Each stage receives the context and pulls its dependencies from
the state's cached outputs via ``get_stage_output()``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Any, Callable
from uuid import UUID

from app.pipeline.schemas import PipelineProgress, PipelineStage

if TYPE_CHECKING:
    from app.pipeline.pipeline_state import PipelineState
    from app.pipeline.schemas import MetricRecord, ReportRequest


@dataclass
class PipelineContext:
    """
    Shared context passed through all pipeline stages.

    Contains the report request parameters, raw input data, shared
    dependencies, accumulated stage results (via state), and the
    progress callback for real-time status updates.
    """

    # Request identity
    report_id: UUID
    organization_id: UUID
    generated_by: UUID

    # Date range
    date_range_start: date
    date_range_end: date
    comparison_period: str = "previous_period"

    # Configuration
    platforms: list[str] = field(default_factory=list)
    tone: str = "executive"
    ai_model: str = "claude-sonnet-4-6"
    title: str = ""
    template: str = "monthly_performance"

    # Input data
    records: list[MetricRecord] = field(default_factory=list)
    request: ReportRequest | None = None

    # Pipeline state (tracks stage results for inter-stage dependencies)
    state: PipelineState | None = None

    # Dependencies (injected at construction time)
    anthropic_client: Any = None
    progress_callback: Callable[[PipelineProgress], None] | None = None

    # Accumulated metadata
    total_tokens_used: int = 0
    total_ai_cost: float = 0.0

    def get_stage_output(self, stage_name: str) -> Any:
        """Retrieve the cached output of a previously completed stage."""
        if self.state is None:
            raise RuntimeError("PipelineContext has no state attached")
        return self.state.get_output(stage_name)

    def report_progress(self, stage: PipelineStage, pct: int, message: str = "") -> None:
        """Publish a progress update if a callback is registered."""
        if self.progress_callback:
            self.progress_callback(PipelineProgress(
                report_id=self.report_id,
                stage=stage,
                pct=pct,
                message=message,
            ))

    def add_token_usage(self, tokens: int, cost: float = 0.0) -> None:
        """Accumulate AI token usage and cost across stages."""
        self.total_tokens_used += tokens
        self.total_ai_cost += cost
