"""Tests for pipeline execution context."""

from uuid import uuid4

import pytest

from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.schemas import PipelineProgress, PipelineStage


class TestPipelineContext:
    """Pipeline context tests."""

    def test_create_context(self):
        ctx = PipelineContext(
            report_id=uuid4(),
            organization_id=uuid4(),
            generated_by=uuid4(),
            date_range_start="2024-01-01",
            date_range_end="2024-01-31",
        )
        assert ctx.tone == "executive"
        assert ctx.ai_model == "claude-sonnet-4-6"
        assert ctx.total_tokens_used == 0

    def test_add_token_usage(self):
        ctx = PipelineContext(
            report_id=uuid4(),
            organization_id=uuid4(),
            generated_by=uuid4(),
            date_range_start="2024-01-01",
            date_range_end="2024-01-31",
        )
        ctx.add_token_usage(1000, 0.05)
        ctx.add_token_usage(2000, 0.10)
        assert ctx.total_tokens_used == 3000
        assert ctx.total_ai_cost == pytest.approx(0.15)

    def test_progress_callback(self):
        captured = []

        def callback(progress: PipelineProgress):
            captured.append(progress)

        ctx = PipelineContext(
            report_id=uuid4(),
            organization_id=uuid4(),
            generated_by=uuid4(),
            date_range_start="2024-01-01",
            date_range_end="2024-01-31",
            progress_callback=callback,
        )
        ctx.report_progress(PipelineStage.DATA_VALIDATION, 5, "Testing...")

        assert len(captured) == 1
        assert captured[0].pct == 5

    def test_no_callback_does_not_error(self):
        ctx = PipelineContext(
            report_id=uuid4(),
            organization_id=uuid4(),
            generated_by=uuid4(),
            date_range_start="2024-01-01",
            date_range_end="2024-01-31",
        )
        ctx.report_progress(PipelineStage.DATA_VALIDATION, 5)  # Should not raise
