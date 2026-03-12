"""Tests for pipeline state tracking."""

from uuid import uuid4

import pytest

from app.pipeline.pipeline_state import PipelineState, StageStatus


class TestPipelineState:
    """Pipeline state machine tests."""

    def test_initial_state_all_pending(self):
        state = PipelineState(report_id=uuid4())
        for stage_state in state.stages.values():
            assert stage_state.status == StageStatus.PENDING

    def test_mark_running(self):
        state = PipelineState(report_id=uuid4())
        state.mark_running("data_validation")
        assert state.stages["data_validation"].status == StageStatus.RUNNING
        assert state.stages["data_validation"].started_at is not None

    def test_mark_completed(self):
        state = PipelineState(report_id=uuid4())
        state.mark_running("kpi_computation")
        state.mark_completed("kpi_computation", output={"test": True})
        assert state.stages["kpi_computation"].status == StageStatus.COMPLETED
        assert state.stages["kpi_computation"].output == {"test": True}
        assert state.stages["kpi_computation"].duration_ms >= 0

    def test_mark_failed(self):
        state = PipelineState(report_id=uuid4())
        state.mark_running("trend_detection")
        state.mark_failed("trend_detection", "Test error")
        assert state.stages["trend_detection"].status == StageStatus.FAILED
        assert state.stages["trend_detection"].error == "Test error"

    def test_is_completed(self):
        state = PipelineState(report_id=uuid4())
        assert not state.is_completed("data_validation")
        state.mark_running("data_validation")
        state.mark_completed("data_validation")
        assert state.is_completed("data_validation")

    def test_is_finished(self):
        state = PipelineState(report_id=uuid4())
        assert not state.is_finished
        for stage_name in PipelineState.STAGE_ORDER:
            state.mark_running(stage_name)
            state.mark_completed(stage_name)
        assert state.is_finished

    def test_has_failures(self):
        state = PipelineState(report_id=uuid4())
        assert not state.has_failures
        state.mark_running("insight_generation")
        state.mark_failed("insight_generation", "AI timeout")
        assert state.has_failures

    def test_summary(self):
        state = PipelineState(report_id=uuid4())
        state.mark_running("data_validation")
        state.mark_completed("data_validation")
        summary = state.summary()
        assert summary["data_validation"] == "completed"
        assert summary["kpi_computation"] == "pending"

    def test_timing_report(self):
        state = PipelineState(report_id=uuid4())
        state.mark_running("data_validation")
        state.mark_completed("data_validation")
        timing = state.timing_report()
        assert "data_validation" in timing
        assert "kpi_computation" not in timing
