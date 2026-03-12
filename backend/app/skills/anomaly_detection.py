"""
Anomaly Detection skill — Z-score, IQR, contextual, and correlation-break detection.

Detects outliers, pattern breaks, and correlation anomalies in marketing metrics.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import date, timedelta

from app.pipeline.schemas import (
    AnomalyPoint,
    AnomalyType,
    CorrelationAnomaly,
    DatedValue,
    Severity,
)


REVENUE_METRICS = {"spend", "conversions", "conversion_value", "roas", "cpa"}


def classify_severity(z_score: float, metric_id: str) -> Severity:
    """Classify anomaly severity based on z-score and metric importance."""
    z = abs(z_score)
    is_revenue = metric_id in REVENUE_METRICS

    if z > 4.0 or (is_revenue and z > 3.0):
        return Severity.CRITICAL
    elif z > 3.0 or (is_revenue and z > 2.5):
        return Severity.HIGH
    elif z > 2.5:
        return Severity.MEDIUM
    return Severity.LOW


class ZScoreDetector:
    """Detects anomalies where |z-score| exceeds threshold using a rolling baseline."""

    def detect(
        self,
        timeseries: list[float],
        metric_name: str = "",
        threshold: float = 2.5,
        rolling_window: int = 30,
        dates: list[date] | None = None,
    ) -> list[AnomalyPoint]:
        anomalies = []
        for i in range(rolling_window, len(timeseries)):
            window = timeseries[i - rolling_window : i]
            mean = statistics.mean(window)
            std = statistics.stdev(window) if len(window) > 1 else 0

            if std == 0:
                continue

            z_score = (timeseries[i] - mean) / std

            if abs(z_score) > threshold:
                anomalies.append(AnomalyPoint(
                    metric=metric_name,
                    index=i,
                    anomaly_date=dates[i] if dates else None,
                    value=round(timeseries[i], 2),
                    expected=round(mean, 2),
                    z_score=round(z_score, 2),
                    type=AnomalyType.SPIKE if z_score > 0 else AnomalyType.DROP,
                    severity=classify_severity(z_score, metric_name),
                    deviation_pct=round(((timeseries[i] - mean) / mean) * 100, 1) if mean != 0 else None,
                ))
        return anomalies


class IQRDetector:
    """Detects outliers using Interquartile Range — robust for non-normal distributions."""

    def detect(
        self,
        timeseries: list[float],
        metric_name: str = "",
        multiplier: float = 1.5,
        dates: list[date] | None = None,
    ) -> list[AnomalyPoint]:
        if len(timeseries) < 4:
            return []

        sorted_vals = sorted(timeseries)
        n = len(sorted_vals)
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[3 * n // 4]
        iqr = q3 - q1
        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr

        anomalies = []
        mean_val = statistics.mean(timeseries)

        for i, v in enumerate(timeseries):
            if v < lower or v > upper:
                atype = AnomalyType.SPIKE if v > upper else AnomalyType.DROP
                z_approx = (v - mean_val) / statistics.stdev(timeseries) if statistics.stdev(timeseries) > 0 else 0
                anomalies.append(AnomalyPoint(
                    metric=metric_name,
                    index=i,
                    anomaly_date=dates[i] if dates else None,
                    value=round(v, 2),
                    expected=round(mean_val, 2),
                    z_score=round(z_approx, 2),
                    type=atype,
                    severity=classify_severity(z_approx, metric_name),
                ))
        return anomalies


class ContextualDetector:
    """Detects values unusual for their specific day-of-week context."""

    def detect(
        self,
        dated_values: list[DatedValue],
        metric_name: str = "",
        threshold: float = 2.0,
    ) -> list[AnomalyPoint]:
        by_dow: dict[int, list[float]] = defaultdict(list)
        for dv in dated_values:
            by_dow[dv.date.weekday()].append(dv.value)

        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        anomalies = []

        for i, dv in enumerate(dated_values):
            dow = dv.date.weekday()
            dow_values = by_dow[dow]
            if len(dow_values) < 3:
                continue

            dow_mean = statistics.mean(dow_values)
            dow_std = statistics.stdev(dow_values)
            if dow_std == 0:
                continue

            z = (dv.value - dow_mean) / dow_std
            if abs(z) > threshold:
                anomalies.append(AnomalyPoint(
                    metric=metric_name,
                    index=i,
                    anomaly_date=dv.date,
                    value=round(dv.value, 2),
                    expected=round(dow_mean, 2),
                    z_score=round(z, 2),
                    type=AnomalyType.SPIKE if z > 0 else AnomalyType.DROP,
                    severity=classify_severity(z, metric_name),
                    context=f"Unusual for {day_names[dow]}",
                ))
        return anomalies


class CorrelationBreakDetector:
    """Detects when normally correlated metrics diverge."""

    EXPECTED_CORRELATIONS = {
        ("impressions", "clicks"): {"direction": "positive", "min_r": 0.6},
        ("spend", "conversions"): {"direction": "positive", "min_r": 0.4},
        ("clicks", "conversions"): {"direction": "positive", "min_r": 0.3},
    }

    def detect(
        self,
        metrics: dict[str, list[float]],
        window: int = 14,
    ) -> list[CorrelationAnomaly]:
        anomalies = []
        for (m1, m2), _expected in self.EXPECTED_CORRELATIONS.items():
            if m1 not in metrics or m2 not in metrics:
                continue
            if len(metrics[m1]) < window + 7:
                continue

            historical_r = _correlation(metrics[m1][:-window], metrics[m2][:-window])
            recent_r = _correlation(metrics[m1][-window:], metrics[m2][-window:])

            if historical_r is not None and recent_r is not None:
                if abs(historical_r - recent_r) > 0.4:
                    anomalies.append(CorrelationAnomaly(
                        metric_pair=(m1, m2),
                        historical_correlation=round(historical_r, 2),
                        recent_correlation=round(recent_r, 2),
                        significance="high" if abs(historical_r - recent_r) > 0.6 else "medium",
                    ))
        return anomalies


class MissingDataDetector:
    """Detects dates that should have data but don't."""

    def detect(
        self,
        dates_with_data: list[date],
        expected_start: date,
        expected_end: date,
    ) -> list[date]:
        expected = set()
        current = expected_start
        while current <= expected_end:
            expected.add(current)
            current += timedelta(days=1)
        actual = set(dates_with_data)
        return sorted(expected - actual)


def _correlation(x: list[float], y: list[float]) -> float | None:
    """Compute Pearson correlation coefficient."""
    n = min(len(x), len(y))
    if n < 3:
        return None

    x, y = x[:n], y[:n]
    x_mean = statistics.mean(x)
    y_mean = statistics.mean(y)

    ss_xy = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    ss_xx = sum((xi - x_mean) ** 2 for xi in x)
    ss_yy = sum((yi - y_mean) ** 2 for yi in y)

    denom = (ss_xx * ss_yy) ** 0.5
    if denom == 0:
        return None
    return ss_xy / denom
