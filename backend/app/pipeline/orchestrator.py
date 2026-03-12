"""
Pipeline Orchestrator — DAG-based execution of the analytics pipeline.

Coordinates all 8 agents in dependency order with maximum parallelism:

  Stage 1: Data Validation
  Stage 2: KPI Computation
  Stages 3+4 (parallel): Trend Detection + Anomaly Detection
  Stage 5: Campaign Evaluation
  Stage 6: Insight Generation
  Stage 7: Recommendation Generation
  Stage 8: Report Assembly

Total target: < 45 seconds for a complete report.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable

from app.agents.anomaly_detection_agent import (
    AnomalyDetectionAgent,
    AnomalyDetectionInput,
)
from app.agents.campaign_evaluation_agent import (
    CampaignEvaluationAgent,
    CampaignEvaluationInput,
)
from app.agents.data_validation_agent import (
    DataValidationAgent,
    DataValidationInput,
)
from app.agents.insight_generation_agent import (
    InsightGenerationAgent,
    InsightGenerationInput,
)
from app.agents.kpi_computation_agent import (
    KPIComputationAgent,
    KPIComputationInput,
)
from app.agents.recommendation_agent import (
    RecommendationAgent,
    RecommendationInput,
)
from app.agents.report_generation_agent import (
    ReportAssemblyInput,
    ReportGenerationAgent,
)
from app.agents.trend_detection_agent import (
    TrendDetectionAgent,
    TrendDetectionInput,
)
from app.pipeline.schemas import (
    MetricRecord,
    PipelineProgress,
    PipelineResult,
    PipelineStage,
    ReportRequest,
)

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    DAG-based orchestrator for the InsightFlow analytics pipeline.

    Executes 8 pipeline stages in dependency order, running independent
    stages in parallel where the DAG allows.
    """

    def __init__(self, anthropic_client=None) -> None:
        self._anthropic_client = anthropic_client

        # Initialize all agents
        self._data_validation = DataValidationAgent()
        self._kpi_computation = KPIComputationAgent()
        self._trend_detection = TrendDetectionAgent()
        self._anomaly_detection = AnomalyDetectionAgent()
        self._campaign_evaluation = CampaignEvaluationAgent()
        self._insight_generation = InsightGenerationAgent(anthropic_client)
        self._recommendation = RecommendationAgent(anthropic_client)
        self._report_generation = ReportGenerationAgent()

    async def execute(
        self,
        request: ReportRequest,
        records: list[MetricRecord],
        progress_callback: Callable[[PipelineProgress], None] | None = None,
    ) -> PipelineResult:
        """
        Execute the full analytics pipeline.

        Args:
            request: Report generation request parameters.
            records: Raw metric records to analyze (both current + previous period).
            progress_callback: Optional callback for progress updates.

        Returns:
            PipelineResult containing all analysis outputs.
        """
        start_time = time.monotonic()

        def _progress(stage: PipelineStage, pct: int, message: str = "") -> None:
            if progress_callback:
                progress_callback(PipelineProgress(
                    report_id=request.report_id,
                    stage=stage,
                    pct=pct,
                    message=message,
                ))

        # ── Stage 1: Data Validation ────────────────────────────
        _progress(PipelineStage.DATA_VALIDATION, 5, "Validating data...")
        validation = await self._data_validation.run(
            DataValidationInput(records=records)
        )

        if not validation.is_valid:
            logger.warning(
                "Data validation has %d errors — continuing with valid records",
                len(validation.errors),
            )

        # ── Stage 2: KPI Computation ────────────────────────────
        _progress(PipelineStage.KPI_COMPUTATION, 15, "Computing KPIs...")
        kpis = await self._kpi_computation.run(
            KPIComputationInput(
                records=records,
                date_range_start=request.date_range_start,
                date_range_end=request.date_range_end,
                comparison_period=request.comparison_period,
            )
        )

        # ── Stages 3+4 (parallel): Trends + Anomalies ──────────
        _progress(PipelineStage.TREND_DETECTION, 25, "Detecting trends and anomalies...")
        trend_task = self._trend_detection.run(
            TrendDetectionInput(records=kpis.records)
        )
        anomaly_task = self._anomaly_detection.run(
            AnomalyDetectionInput(records=kpis.records)
        )
        trends, anomalies = await asyncio.gather(trend_task, anomaly_task)

        # ── Stage 5: Campaign Evaluation ────────────────────────
        _progress(PipelineStage.CAMPAIGN_EVALUATION, 40, "Evaluating campaigns...")
        evaluation = await self._campaign_evaluation.run(
            CampaignEvaluationInput(kpis=kpis)
        )

        # ── Stage 6: Insight Generation ─────────────────────────
        _progress(PipelineStage.INSIGHT_GENERATION, 55, "Generating insights...")
        insights = await self._insight_generation.run(
            InsightGenerationInput(
                kpis=kpis,
                trends=trends,
                anomalies=anomalies,
                evaluation=evaluation,
                tone=request.tone,
                ai_model=request.ai_model,
            )
        )

        # ── Stage 7: Recommendation Generation ──────────────────
        _progress(PipelineStage.RECOMMENDATION_GENERATION, 70, "Generating recommendations...")
        recommendations = await self._recommendation.run(
            RecommendationInput(
                kpis=kpis,
                trends=trends,
                anomalies=anomalies,
                evaluation=evaluation,
                insights=insights,
                tone=request.tone,
                ai_model=request.ai_model,
            )
        )

        # ── Stage 8: Report Assembly ────────────────────────────
        _progress(PipelineStage.REPORT_ASSEMBLY, 90, "Assembling report...")
        result = await self._report_generation.run(
            ReportAssemblyInput(
                request=request,
                validation=validation,
                kpis=kpis,
                trends=trends,
                anomalies=anomalies,
                evaluation=evaluation,
                insights=insights,
                recommendations=recommendations,
            )
        )

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            "Pipeline completed for report %s in %dms",
            request.report_id,
            elapsed_ms,
        )

        return result
