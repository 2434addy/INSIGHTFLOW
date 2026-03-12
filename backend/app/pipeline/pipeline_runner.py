"""
Pipeline Runner — production-grade DAG execution engine.

Orchestrates 8 pipeline stages via the ``BaseStage.run(context)`` interface.
Supports async execution with timeout, dependency-graph-driven parallelism,
pipeline state tracking with resumability, structured logging, and domain
event publishing.

Usage:
    runner = PipelineRunner(anthropic_client=client)
    result = await runner.run(request, records, progress_callback=cb)

    # Or with event publishing:
    runner = PipelineRunner(anthropic_client=client, event_bus=event_bus)
    result = await runner.run(request, records)
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable
from uuid import UUID

import structlog

from app.core.config import get_settings
from app.pipeline.pipeline_context import PipelineContext
from app.pipeline.pipeline_state import PipelineState, StageStatus
from app.pipeline.schemas import (
    AnomalyAnalysis,
    CampaignEvaluationResult,
    InsightGenerationResult,
    MetricRecord,
    PipelineProgress,
    PipelineResult,
    PipelineStage,
    RecommendationResult,
    ReportRequest,
    TrendAnalysis,
)
from app.pipeline.stages import BaseStage
from app.pipeline.stages.stage_anomaly import AnomalyDetectionStage
from app.pipeline.stages.stage_evaluation import CampaignEvaluationStage
from app.pipeline.stages.stage_insight import InsightGenerationStage
from app.pipeline.stages.stage_kpi import KPIComputationStage
from app.pipeline.stages.stage_recommendation import RecommendationGenerationStage
from app.pipeline.stages.stage_report import ReportAssemblyStage
from app.pipeline.stages.stage_trend import TrendDetectionStage
from app.pipeline.stages.stage_validation import DataValidationStage

logger = structlog.get_logger(__name__)
settings = get_settings()


class PipelineError(Exception):
    """Raised when the pipeline fails in a non-recoverable way."""

    def __init__(self, message: str, stage: str, report_id: UUID) -> None:
        self.stage = stage
        self.report_id = report_id
        super().__init__(message)


class PipelineTimeoutError(PipelineError):
    """Raised when the pipeline exceeds the configured timeout."""
    pass


class PipelineValidationError(PipelineError):
    """Raised when input validation fails catastrophically."""
    pass


# ── Dependency Graph ──────────────────────────────────────────────────
#
# The DAG defines which stages can run after which. Stages 3 and 4 share
# the same dependency (stage 2) and no dependency on each other, so they
# run in parallel.
#
#   1 → 2 → 3 ──┐
#           ↘ 4 ─┤→ 5 → 6 → 7 → 8
#

STAGE_DEPS: dict[str, list[str]] = {
    "data_validation": [],
    "kpi_computation": ["data_validation"],
    "trend_detection": ["kpi_computation"],
    "anomaly_detection": ["kpi_computation"],
    "campaign_evaluation": ["trend_detection", "anomaly_detection"],
    "insight_generation": ["campaign_evaluation"],
    "recommendation_generation": ["insight_generation"],
    "report_assembly": ["recommendation_generation"],
}

# Stages that must succeed for the pipeline to produce any output.
# Non-critical stages use fallback (empty) outputs on failure.
CRITICAL_STAGES: frozenset[str] = frozenset({
    "data_validation",
    "kpi_computation",
    "report_assembly",
})

# Default empty outputs for non-critical stages when they fail.
_STAGE_FALLBACKS: dict[str, Any] = {
    "trend_detection": TrendAnalysis(),
    "anomaly_detection": AnomalyAnalysis(),
    "campaign_evaluation": CampaignEvaluationResult(),
    "insight_generation": InsightGenerationResult(),
    "recommendation_generation": RecommendationResult(),
}

STAGE_PROGRESS: dict[str, tuple[PipelineStage, int, str]] = {
    "data_validation": (PipelineStage.DATA_VALIDATION, 5, "Validating data..."),
    "kpi_computation": (PipelineStage.KPI_COMPUTATION, 15, "Computing KPIs..."),
    "trend_detection": (PipelineStage.TREND_DETECTION, 30, "Detecting trends..."),
    "anomaly_detection": (PipelineStage.ANOMALY_DETECTION, 30, "Detecting anomalies..."),
    "campaign_evaluation": (PipelineStage.CAMPAIGN_EVALUATION, 45, "Evaluating campaigns..."),
    "insight_generation": (PipelineStage.INSIGHT_GENERATION, 60, "Generating insights..."),
    "recommendation_generation": (PipelineStage.RECOMMENDATION_GENERATION, 75, "Generating recommendations..."),
    "report_assembly": (PipelineStage.REPORT_ASSEMBLY, 90, "Assembling report..."),
}


class PipelineRunner:
    """
    Production-grade analytics pipeline runner.

    Executes 8 stages in DAG order with parallel execution where the
    dependency graph allows. Each stage implements ``BaseStage.run(context)``
    and pulls its upstream dependencies from the shared context/state.
    """

    def __init__(
        self,
        anthropic_client: Any = None,
        event_bus: Any = None,
        timeout: int | None = None,
        max_records: int | None = None,
    ) -> None:
        self._anthropic_client = anthropic_client
        self._event_bus = event_bus
        self._timeout = timeout or settings.PIPELINE_TIMEOUT
        self._max_records = max_records or settings.PIPELINE_MAX_RECORDS

        # Initialize stage instances
        self._stages: dict[str, BaseStage] = {
            "data_validation": DataValidationStage(),
            "kpi_computation": KPIComputationStage(),
            "trend_detection": TrendDetectionStage(),
            "anomaly_detection": AnomalyDetectionStage(),
            "campaign_evaluation": CampaignEvaluationStage(),
            "insight_generation": InsightGenerationStage(),
            "recommendation_generation": RecommendationGenerationStage(),
            "report_assembly": ReportAssemblyStage(),
        }

    async def run(
        self,
        request: ReportRequest,
        records: list[MetricRecord],
        progress_callback: Callable[[PipelineProgress], None] | None = None,
        state: PipelineState | None = None,
    ) -> PipelineResult:
        """
        Execute the full analytics pipeline.

        Args:
            request: Report generation request parameters.
            records: Raw metric records to process.
            progress_callback: Optional callback for real-time progress.
            state: Optional pre-existing state for resuming a failed run.

        Returns:
            PipelineResult with all stage outputs.

        Raises:
            PipelineTimeoutError: If execution exceeds the configured timeout.
            PipelineValidationError: If input data fails critical validation.
            PipelineError: If a stage fails without recovery.
        """
        start_time = time.monotonic()

        log = logger.bind(
            report_id=str(request.report_id),
            organization_id=str(request.organization_id),
        )

        # ── Input validation ──────────────────────────────────
        self._validate_input(request, records, log)

        # ── Build context and state ───────────────────────────
        if state is None:
            state = PipelineState(report_id=request.report_id)

        context = PipelineContext(
            report_id=request.report_id,
            organization_id=request.organization_id,
            generated_by=request.generated_by,
            date_range_start=request.date_range_start,
            date_range_end=request.date_range_end,
            comparison_period=request.comparison_period,
            platforms=request.platforms,
            tone=request.tone,
            ai_model=request.ai_model,
            title=request.title,
            template=request.template,
            records=records,
            request=request,
            state=state,
            anthropic_client=self._anthropic_client,
            progress_callback=progress_callback,
        )

        await log.ainfo(
            "Pipeline starting",
            num_records=len(records),
            date_range=f"{request.date_range_start} → {request.date_range_end}",
            ai_model=request.ai_model,
            tone=request.tone,
            timeout=self._timeout,
        )

        # ── Execute with timeout ──────────────────────────────
        try:
            result = await asyncio.wait_for(
                self._execute_dag(context, state, log),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            await log.aerror(
                "Pipeline timed out",
                elapsed_ms=elapsed_ms,
                timeout=self._timeout,
                stages=state.summary(),
            )
            await self._publish_failure(
                request, f"Pipeline timed out after {self._timeout}s", "timeout", state
            )
            raise PipelineTimeoutError(
                f"Pipeline timed out after {self._timeout}s",
                stage="timeout",
                report_id=request.report_id,
            )
        except PipelineError:
            raise
        except Exception as exc:
            failed_stage = self._find_failed_stage(state)
            await log.aerror(
                "Pipeline failed with unexpected error",
                error=str(exc),
                stage=failed_stage,
                stages=state.summary(),
            )
            await self._publish_failure(request, str(exc), failed_stage, state)
            raise PipelineError(
                str(exc), stage=failed_stage, report_id=request.report_id
            ) from exc

        # ── Finalize ──────────────────────────────────────────
        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        result.total_tokens_used = context.total_tokens_used
        result.total_ai_cost = context.total_ai_cost

        await log.ainfo(
            "Pipeline completed",
            elapsed_ms=elapsed_ms,
            total_tokens=context.total_tokens_used,
            total_ai_cost=round(context.total_ai_cost, 4),
            timing=state.timing_report(),
            stages=state.summary(),
        )

        context.report_progress(PipelineStage.REPORT_ASSEMBLY, 100, "Complete")

        await self._publish_success(request, context, state)

        return result

    # ── DAG Execution ─────────────────────────────────────────────

    async def _execute_dag(
        self,
        context: PipelineContext,
        state: PipelineState,
        log: Any,
    ) -> PipelineResult:
        """
        Execute all 8 stages respecting the dependency graph.

        Stages 3 (trends) and 4 (anomalies) run in parallel because
        they depend only on stage 2 and not on each other.
        """
        # ── Stage 1: Data Validation ──────────────────────────
        validation = await self._run_stage("data_validation", context, state, log)

        if validation.error_rate > 0.5:
            raise PipelineValidationError(
                f"Data validation failed: {len(validation.errors)} errors "
                f"in {validation.total_records} records ({validation.error_rate:.0%} error rate)",
                stage="data_validation",
                report_id=context.report_id,
            )

        if not validation.is_valid:
            await log.awarning(
                "Data validation has errors — continuing with valid records",
                error_count=len(validation.errors),
                warning_count=len(validation.warnings),
                error_rate=round(validation.error_rate, 3),
            )

        # ── Stage 2: KPI Computation ──────────────────────────
        await self._run_stage("kpi_computation", context, state, log)

        # ── Stages 3+4 (parallel): Trends + Anomalies ────────
        trend_task = self._run_stage("trend_detection", context, state, log)
        anomaly_task = self._run_stage("anomaly_detection", context, state, log)
        await asyncio.gather(trend_task, anomaly_task)

        # ── Stage 5: Campaign Evaluation ──────────────────────
        await self._run_stage("campaign_evaluation", context, state, log)

        # ── Stage 6: Insight Generation ───────────────────────
        await self._run_stage("insight_generation", context, state, log)

        # ── Stage 7: Recommendation Generation ────────────────
        await self._run_stage("recommendation_generation", context, state, log)

        # ── Stage 8: Report Assembly ──────────────────────────
        result = await self._run_stage("report_assembly", context, state, log)

        return result

    # ── Stage Runner (state tracking + resumability) ──────────────

    async def _run_stage(
        self,
        stage_name: str,
        context: PipelineContext,
        state: PipelineState,
        log: Any,
    ) -> Any:
        """
        Execute a single stage with state tracking and resumability.

        If the stage was already completed in a previous run (resuming),
        returns the cached output without re-executing.
        """
        # Skip if already completed (resumability)
        if state.is_completed(stage_name):
            await log.ainfo("Skipping completed stage", stage=stage_name)
            return state.get_output(stage_name)

        # Report progress
        stage_enum, pct, message = STAGE_PROGRESS[stage_name]
        context.report_progress(stage_enum, pct, message)

        # Execute via BaseStage.run(context)
        state.mark_running(stage_name)
        stage_start = time.monotonic()

        try:
            stage = self._stages[stage_name]
            result = await stage.run(context)
            stage_ms = int((time.monotonic() - stage_start) * 1000)
            state.mark_completed(stage_name, result)

            await log.ainfo(
                "Stage completed",
                stage=stage_name,
                duration_ms=stage_ms,
            )

            return result

        except Exception as exc:
            stage_ms = int((time.monotonic() - stage_start) * 1000)

            # Non-critical stages produce fallback outputs instead of
            # crashing the pipeline.
            if stage_name not in CRITICAL_STAGES and stage_name in _STAGE_FALLBACKS:
                fallback = _STAGE_FALLBACKS[stage_name]
                state.mark_completed(stage_name, fallback)

                await log.awarning(
                    "Stage failed — using fallback output",
                    stage=stage_name,
                    duration_ms=stage_ms,
                    error=str(exc),
                    error_type=type(exc).__name__,
                )

                return fallback

            state.mark_failed(stage_name, str(exc))

            await log.aerror(
                "Stage failed",
                stage=stage_name,
                duration_ms=stage_ms,
                error=str(exc),
                error_type=type(exc).__name__,
            )

            raise PipelineError(
                f"Stage '{stage_name}' failed: {exc}",
                stage=stage_name,
                report_id=context.report_id,
            ) from exc

    # ── Input Validation ──────────────────────────────────────────

    def _validate_input(
        self,
        request: ReportRequest,
        records: list[MetricRecord],
        log: Any,
    ) -> None:
        """Validate inputs before pipeline execution starts."""
        if not records:
            raise PipelineValidationError(
                "No metric records provided",
                stage="input_validation",
                report_id=request.report_id,
            )

        if len(records) > self._max_records:
            raise PipelineValidationError(
                f"Too many records: {len(records)} exceeds limit of {self._max_records}",
                stage="input_validation",
                report_id=request.report_id,
            )

        if request.date_range_start > request.date_range_end:
            raise PipelineValidationError(
                f"Invalid date range: {request.date_range_start} > {request.date_range_end}",
                stage="input_validation",
                report_id=request.report_id,
            )

    # ── Event Publishing ──────────────────────────────────────────

    async def _publish_success(
        self,
        request: ReportRequest,
        context: PipelineContext,
        state: PipelineState,
    ) -> None:
        """Publish a ReportCompleted event if an event bus is configured."""
        if not self._event_bus:
            return

        from app.events.event_bus import ReportCompleted

        await self._event_bus.publish(ReportCompleted(
            report_id=request.report_id,
            organization_id=request.organization_id,
            total_tokens=context.total_tokens_used,
            ai_cost=context.total_ai_cost,
        ))

    async def _publish_failure(
        self,
        request: ReportRequest,
        error: str,
        stage: str,
        state: PipelineState,
    ) -> None:
        """Publish a ReportFailed event if an event bus is configured."""
        if not self._event_bus:
            return

        from app.events.event_bus import ReportFailed

        await self._event_bus.publish(ReportFailed(
            report_id=request.report_id,
            organization_id=request.organization_id,
            error=error,
            stage=stage,
        ))

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _find_failed_stage(state: PipelineState) -> str:
        """Find the name of the stage that caused the failure."""
        for name, stage_state in state.stages.items():
            if stage_state.status in (StageStatus.RUNNING, StageStatus.FAILED):
                return name
        return "unknown"
