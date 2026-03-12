"""
Data Analysis Agent — composite agent for KPI computation, trend
detection, and anomaly detection.

Combines three analytical responsibilities into a single agent that
delegates to the underlying skills:

- **KPI computation** — derived metrics (CTR, CPC, CPA, ROAS),
  aggregation by platform/campaign, period-over-period comparison.
- **Trend detection** — OLS-based trend classification, moving
  averages, budget pacing analysis.
- **Anomaly detection** — Z-score outliers, day-of-week contextual
  anomalies, correlation breaks, and missing data detection.

Usage:
    agent = DataAnalysisAgent()
    result = await agent.run(DataAnalysisInput(
        records=records,
        date_range_start=date(2026, 2, 1),
        date_range_end=date(2026, 2, 28),
    ))
    result.kpis   # KPIResult
    result.trends  # TrendAnalysis
    result.anomalies  # AnomalyAnalysis
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from app.agents.base import BaseAgent
from app.pipeline.schemas import (
    AnomalyAnalysis,
    AnomalyType,
    DataAnalysisResult,
    DatedValue,
    KPIResult,
    MetricRecord,
    MovingAverages,
    TrendAnalysis,
)
from app.skills.anomaly_detection import (
    ContextualDetector,
    CorrelationBreakDetector,
    MissingDataDetector,
    ZScoreDetector,
)
from app.skills.kpi_computation import Aggregator, KPIComputer, PeriodComparer
from app.skills.trend_detection import (
    MovingAverageAnalyzer,
    PacingAnalyzer,
    TrendClassifier,
)

logger = logging.getLogger(__name__)

ANALYSIS_METRICS = ["spend", "impressions", "clicks", "conversions", "conversion_value"]


@dataclass
class DataAnalysisInput:
    """Input for the DataAnalysisAgent."""

    records: list[MetricRecord]
    date_range_start: date
    date_range_end: date
    comparison_period: str = "previous_period"
    budget: float | None = None
    days_in_period: int = 30


class DataAnalysisAgent(BaseAgent[DataAnalysisInput, DataAnalysisResult]):
    """
    Composite agent that computes KPIs, detects trends, and detects
    anomalies in a single pass over the data.

    Delegates all computation to skills in ``app.skills``.
    """

    name = "data_analysis_agent"
    max_retries = 1

    def __init__(self) -> None:
        # KPI skills
        self._kpi_computer = KPIComputer()
        self._aggregator = Aggregator()
        self._period_comparer = PeriodComparer()

        # Trend skills
        self._trend_classifier = TrendClassifier()
        self._ma_analyzer = MovingAverageAnalyzer()
        self._pacing_analyzer = PacingAnalyzer()

        # Anomaly skills
        self._zscore_detector = ZScoreDetector()
        self._contextual_detector = ContextualDetector()
        self._correlation_detector = CorrelationBreakDetector()
        self._missing_detector = MissingDataDetector()

    async def execute(self, input_data: DataAnalysisInput) -> DataAnalysisResult:
        logger.info(
            "DataAnalysisAgent starting: %d records, %s → %s",
            len(input_data.records),
            input_data.date_range_start,
            input_data.date_range_end,
        )

        kpis = self._compute_kpis(input_data)
        trends = self._detect_trends(kpis.records, input_data)
        anomalies = self._detect_anomalies(kpis.records)

        logger.info(
            "DataAnalysisAgent finished: %d trends, %d anomalies",
            len(trends.trends),
            len(anomalies.point_anomalies),
        )

        return DataAnalysisResult(
            kpis=kpis,
            trends=trends,
            anomalies=anomalies,
        )

    # ── KPI Computation ───────────────────────────────────────────

    def _compute_kpis(self, input_data: DataAnalysisInput) -> KPIResult:
        """Compute derived metrics, aggregate, and compare periods."""
        current_records = [
            r for r in input_data.records
            if input_data.date_range_start <= r.date <= input_data.date_range_end
        ]
        previous_records = self._get_previous_records(
            input_data.records,
            input_data.date_range_start,
            input_data.date_range_end,
            input_data.comparison_period,
        )

        current_records = self._kpi_computer.compute_all(current_records)
        if previous_records:
            previous_records = self._kpi_computer.compute_all(previous_records)

        current_summary = self._aggregator.aggregate_summary(current_records)
        by_platform = self._aggregator.aggregate_by(current_records, "platform")
        by_campaign = self._aggregator.aggregate_by(current_records, "campaign_id")

        previous_summary = None
        comparison = None
        if previous_records:
            previous_summary = self._aggregator.aggregate_summary(previous_records)
            comparison = self._period_comparer.compare(current_summary, previous_summary)

        return KPIResult(
            current_period=current_summary,
            previous_period=previous_summary,
            comparison=comparison,
            by_platform=by_platform,
            by_campaign=by_campaign,
            records=current_records,
        )

    # ── Trend Detection ───────────────────────────────────────────

    def _detect_trends(
        self,
        records: list[MetricRecord],
        input_data: DataAnalysisInput,
    ) -> TrendAnalysis:
        """Classify trends and compute moving averages."""
        sorted_records = sorted(records, key=lambda r: r.date)

        timeseries: dict[str, list[float]] = defaultdict(list)
        for r in sorted_records:
            for metric in ANALYSIS_METRICS:
                timeseries[metric].append(float(getattr(r, metric, 0)))

        trends = [
            self._trend_classifier.classify(values, metric_name=metric)
            for metric, values in timeseries.items()
        ]

        moving_avgs = []
        for metric, values in timeseries.items():
            if len(values) >= 7:
                latest = self._ma_analyzer.latest_averages(values)
                moving_avgs.append(MovingAverages(
                    metric=metric,
                    windows={w: round(v, 2) for w, v in latest.items()},
                ))

        pacing = None
        if input_data.budget and "spend" in timeseries:
            pacing = self._pacing_analyzer.analyze(
                actual_spend=timeseries["spend"],
                budget=input_data.budget,
                days_in_period=input_data.days_in_period,
            )

        return TrendAnalysis(
            trends=trends,
            moving_averages=moving_avgs,
            pacing=pacing,
        )

    # ── Anomaly Detection ─────────────────────────────────────────

    def _detect_anomalies(self, records: list[MetricRecord]) -> AnomalyAnalysis:
        """Run all anomaly detectors and merge results."""
        sorted_records = sorted(records, key=lambda r: r.date)
        if not sorted_records:
            return AnomalyAnalysis()

        timeseries: dict[str, list[float]] = defaultdict(list)
        dated_values: dict[str, list[DatedValue]] = defaultdict(list)
        dates: list[date] = []

        for r in sorted_records:
            dates.append(r.date)
            for metric in ANALYSIS_METRICS:
                val = float(getattr(r, metric, 0))
                timeseries[metric].append(val)
                dated_values[metric].append(DatedValue(date=r.date, value=val))

        # Z-score detection
        all_anomalies = []
        for metric, values in timeseries.items():
            if len(values) > 30:
                all_anomalies.extend(
                    self._zscore_detector.detect(values, metric_name=metric, dates=dates)
                )

        # Contextual detection (day-of-week)
        for metric, dv_list in dated_values.items():
            if len(dv_list) >= 28:
                all_anomalies.extend(
                    self._contextual_detector.detect(dv_list, metric_name=metric)
                )

        # Correlation breaks
        correlation_anomalies = self._correlation_detector.detect(timeseries)

        # Missing data
        missing = self._missing_detector.detect(
            dates_with_data=dates,
            expected_start=sorted_records[0].date,
            expected_end=sorted_records[-1].date,
        )

        # Deduplicate by (metric, date)
        seen: set[tuple[str, str]] = set()
        unique_anomalies = []
        for a in all_anomalies:
            key = (a.metric, str(a.anomaly_date))
            if key not in seen:
                seen.add(key)
                unique_anomalies.append(a)

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        unique_anomalies.sort(key=lambda a: severity_order.get(a.severity.value, 4))

        return AnomalyAnalysis(
            point_anomalies=unique_anomalies,
            correlation_anomalies=correlation_anomalies,
            missing_dates=missing,
        )

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _get_previous_records(
        all_records: list[MetricRecord],
        start: date,
        end: date,
        comparison_period: str,
    ) -> list[MetricRecord]:
        period_length = (end - start).days + 1

        if comparison_period == "previous_year":
            prev_start = start.replace(year=start.year - 1)
            prev_end = prev_start + timedelta(days=period_length - 1)
        else:
            prev_end = start - timedelta(days=1)
            prev_start = prev_end - timedelta(days=period_length - 1)

        return [r for r in all_records if prev_start <= r.date <= prev_end]
