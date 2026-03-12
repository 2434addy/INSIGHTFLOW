"""
Pipeline execution context.

Carries shared state, configuration, and dependencies through all pipeline
stages. Avoids passing the same parameters to every agent call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable
from uuid import UUID

from app.pipeline.schemas import PipelineProgress, PipelineStage


@dataclass
class PipelineContext:
    """
    Immutable context passed through all pipeline stages.

    Contains the report request parameters, shared dependencies,
    and the progress callback for real-time status updates.
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

    # Dependencies (injected at construction time)
    anthropic_client: Any = None
    progress_callback: Callable[[PipelineProgress], None] | None = None

    # Accumulated metadata
    total_tokens_used: int = 0
    total_ai_cost: float = 0.0

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
