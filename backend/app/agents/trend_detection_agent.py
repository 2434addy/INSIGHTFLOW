"""
Trend Detection Agent — Stage 3 of the analytics pipeline.

Analyzes metric time-series for trends, moving averages, pacing, and seasonality.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from app.agents.base import BaseAgent
from app.pipeline.schemas import (
    DatedValue,
    MetricRecord,
    MovingAverages,
    TrendAnalysis,
)
from app.skills.trend_detection import (
    MovingAverageAnalyzer,
    PacingAnalyzer,
    SeasonalityDetector,
    TrendClassifier,
)


TREND_METRICS = ["spend", "impressions", "clicks", "conversions", "conversion_value"]


@dataclass
class TrendDetectionInput:
    records: list[MetricRecord]
    budget: float | None = None
    days_in_period: int = 30


class TrendDetectionAgent(BaseAgent[TrendDetectionInput, TrendAnalysis]):
    """Detects trends across all key metrics."""

    name = "trend_detection_agent"

    def __init__(self) -> None:
        self._classifier = TrendClassifier()
        self._ma_analyzer = MovingAverageAnalyzer()
        self._pacing = PacingAnalyzer()
        self._seasonality = SeasonalityDetector()

    async def execute(self, input_data: TrendDetectionInput) -> TrendAnalysis:
        # Sort records by date
        sorted_records = sorted(input_data.records, key=lambda r: r.date)

        # Build time-series per metric
        timeseries: dict[str, list[float]] = defaultdict(list)
        for r in sorted_records:
            for metric in TREND_METRICS:
                timeseries[metric].append(float(getattr(r, metric, 0)))

        # Classify trends
        trends = []
        for metric, values in timeseries.items():
            trend = self._classifier.classify(values, metric_name=metric)
            trends.append(trend)

        # Moving averages (use latest values)
        moving_avgs = []
        for metric, values in timeseries.items():
            if len(values) >= 7:
                latest = self._ma_analyzer.latest_averages(values)
                moving_avgs.append(MovingAverages(
                    metric=metric,
                    windows={w: round(v, 2) for w, v in latest.items()},
                ))

        # Pacing analysis (if budget provided)
        pacing = None
        if input_data.budget and "spend" in timeseries:
            pacing = self._pacing.analyze(
                actual_spend=timeseries["spend"],
                budget=input_data.budget,
                days_in_period=input_data.days_in_period,
            )

        return TrendAnalysis(
            trends=trends,
            moving_averages=moving_avgs,
            pacing=pacing,
        )
