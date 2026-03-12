"""
Anomaly Detection Agent — Stage 4 of the analytics pipeline.

Detects metric outliers, correlation breaks, and missing data using
multiple detection algorithms.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from app.agents.base import BaseAgent
from app.pipeline.schemas import (
    AnomalyAnalysis,
    DatedValue,
    MetricRecord,
)
from app.skills.anomaly_detection import (
    ContextualDetector,
    CorrelationBreakDetector,
    MissingDataDetector,
    ZScoreDetector,
)


ANOMALY_METRICS = ["spend", "impressions", "clicks", "conversions", "conversion_value"]


@dataclass
class AnomalyDetectionInput:
    records: list[MetricRecord]


class AnomalyDetectionAgent(BaseAgent[AnomalyDetectionInput, AnomalyAnalysis]):
    """Detects anomalies across all key metrics."""

    name = "anomaly_detection_agent"

    def __init__(self) -> None:
        self._zscore = ZScoreDetector()
        self._contextual = ContextualDetector()
        self._correlation = CorrelationBreakDetector()
        self._missing = MissingDataDetector()

    async def execute(self, input_data: AnomalyDetectionInput) -> AnomalyAnalysis:
        sorted_records = sorted(input_data.records, key=lambda r: r.date)
        if not sorted_records:
            return AnomalyAnalysis()

        # Build time-series and dated values per metric
        timeseries: dict[str, list[float]] = defaultdict(list)
        dated_values: dict[str, list[DatedValue]] = defaultdict(list)
        dates: list = []

        for r in sorted_records:
            dates.append(r.date)
            for metric in ANOMALY_METRICS:
                val = float(getattr(r, metric, 0))
                timeseries[metric].append(val)
                dated_values[metric].append(DatedValue(date=r.date, value=val))

        # Z-score detection
        all_anomalies = []
        for metric, values in timeseries.items():
            if len(values) > 30:
                anomalies = self._zscore.detect(
                    values,
                    metric_name=metric,
                    dates=dates,
                )
                all_anomalies.extend(anomalies)

        # Contextual detection (day-of-week)
        for metric, dv_list in dated_values.items():
            if len(dv_list) >= 28:  # Need at least 4 weeks
                contextual = self._contextual.detect(dv_list, metric_name=metric)
                all_anomalies.extend(contextual)

        # Correlation break detection
        correlation_anomalies = self._correlation.detect(timeseries)

        # Missing data detection
        missing = self._missing.detect(
            dates_with_data=dates,
            expected_start=sorted_records[0].date,
            expected_end=sorted_records[-1].date,
        )

        # Deduplicate anomalies by (metric, date)
        seen: set[tuple[str, str]] = set()
        unique_anomalies = []
        for a in all_anomalies:
            key = (a.metric, str(a.anomaly_date))
            if key not in seen:
                seen.add(key)
                unique_anomalies.append(a)

        # Sort by severity (critical first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        unique_anomalies.sort(key=lambda a: severity_order.get(a.severity.value, 4))

        return AnomalyAnalysis(
            point_anomalies=unique_anomalies,
            correlation_anomalies=correlation_anomalies,
            missing_dates=missing,
        )
