"""
Trend Detection skill — moving averages, trend classification, pacing analysis.

Provides statistical trend detection algorithms for marketing metrics
time-series data.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import date

from app.pipeline.schemas import (
    DatedValue,
    MovingAverages,
    PacingResult,
    TrendDirection,
    TrendResult,
)


def linear_regression(values: list[float]) -> tuple[float, float, float]:
    """
    Simple linear regression returning (slope, intercept, r_squared).

    Uses the ordinary least squares method.
    """
    n = len(values)
    if n < 2:
        return 0.0, 0.0, 0.0

    x = list(range(n))
    x_mean = statistics.mean(x)
    y_mean = statistics.mean(values)

    ss_xy = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
    ss_xx = sum((xi - x_mean) ** 2 for xi in x)
    ss_yy = sum((yi - y_mean) ** 2 for yi in values)

    if ss_xx == 0:
        return 0.0, y_mean, 0.0

    slope = ss_xy / ss_xx
    intercept = y_mean - slope * x_mean

    if ss_yy == 0:
        r_squared = 0.0
    else:
        r_squared = (ss_xy ** 2) / (ss_xx * ss_yy)

    return slope, intercept, r_squared


class MovingAverageAnalyzer:
    """Computes simple and weighted moving averages."""

    def compute(
        self,
        timeseries: list[float],
        windows: list[int] | None = None,
    ) -> dict[int, list[float]]:
        """Compute simple moving averages for multiple window sizes."""
        windows = windows or [7, 14, 30]
        result: dict[int, list[float]] = {}
        for window in windows:
            ma = []
            for i in range(len(timeseries)):
                start = max(0, i - window + 1)
                segment = timeseries[start : i + 1]
                ma.append(statistics.mean(segment))
            result[window] = ma
        return result

    def latest_averages(
        self, timeseries: list[float], windows: list[int] | None = None
    ) -> dict[int, float]:
        """Return the most recent moving average value for each window."""
        if not timeseries:
            return {}
        all_ma = self.compute(timeseries, windows)
        return {w: values[-1] for w, values in all_ma.items() if values}


class TrendClassifier:
    """Classifies trend direction and strength from time-series data."""

    def classify(
        self,
        timeseries: list[float],
        metric_name: str = "",
        min_data_points: int = 7,
    ) -> TrendResult:
        if len(timeseries) < min_data_points:
            return TrendResult(
                metric=metric_name,
                direction=TrendDirection.INSUFFICIENT_DATA,
            )

        slope, _intercept, r_squared = linear_regression(timeseries)

        mean_value = statistics.mean(timeseries)
        if mean_value == 0:
            return TrendResult(
                metric=metric_name,
                direction=TrendDirection.STABLE,
            )

        normalized_slope = slope / mean_value

        # Classify direction
        if abs(normalized_slope) < 0.005:
            direction = TrendDirection.STABLE
        elif normalized_slope > 0:
            mid = len(timeseries) // 2
            first_slope = linear_regression(timeseries[:mid])[0]
            second_slope = linear_regression(timeseries[mid:])[0]
            direction = (
                TrendDirection.ACCELERATING
                if second_slope > first_slope * 1.2
                else TrendDirection.INCREASING
            )
        else:
            mid = len(timeseries) // 2
            first_slope = linear_regression(timeseries[:mid])[0]
            second_slope = linear_regression(timeseries[mid:])[0]
            direction = (
                TrendDirection.DECLINING
                if second_slope < first_slope * 1.2
                else TrendDirection.DECREASING
            )

        strength = min(1.0, abs(normalized_slope) * 20) * r_squared

        return TrendResult(
            metric=metric_name,
            direction=direction,
            strength=round(strength, 2),
            slope=round(slope, 4),
            normalized_slope_pct=round(normalized_slope * 100, 2),
            r_squared=round(r_squared, 3),
        )


class PacingAnalyzer:
    """Determines if spend is on pace to hit budget."""

    def analyze(
        self,
        actual_spend: list[float],
        budget: float,
        days_in_period: int,
    ) -> PacingResult:
        days_elapsed = len(actual_spend)
        total_spent = sum(actual_spend)
        expected_spent = budget * (days_elapsed / days_in_period) if days_in_period > 0 else 0

        pacing_ratio = total_spent / expected_spent if expected_spent > 0 else 0.0

        if pacing_ratio > 1.15:
            status = "overspending"
        elif pacing_ratio < 0.85:
            status = "underspending"
        else:
            status = "on_track"

        projected = (total_spent / days_elapsed) * days_in_period if days_elapsed > 0 else 0.0

        return PacingResult(
            status=status,
            pacing_ratio=round(pacing_ratio, 2),
            total_spent=round(total_spent, 2),
            expected_spent=round(expected_spent, 2),
            projected_total=round(projected, 2),
            budget=budget,
            days_remaining=days_in_period - days_elapsed,
        )


class SeasonalityDetector:
    """Detects consistent day-of-week patterns in time-series data."""

    def detect_day_of_week_pattern(
        self,
        dated_values: list[DatedValue],
        min_weeks: int = 4,
    ) -> dict | None:
        """Returns day-of-week pattern if significant, else None."""
        if len(dated_values) < min_weeks * 7:
            return None

        by_dow: dict[int, list[float]] = defaultdict(list)
        for dv in dated_values:
            by_dow[dv.date.weekday()].append(dv.value)

        all_values = [dv.value for dv in dated_values]
        total_variance = statistics.variance(all_values) if len(all_values) > 1 else 0
        if total_variance == 0:
            return None

        dow_means = {dow: statistics.mean(vals) for dow, vals in by_dow.items()}
        dow_variance = statistics.variance(dow_means.values()) if len(dow_means) > 1 else 0

        if dow_variance / total_variance > 0.15:
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            return {
                "type": "day_of_week",
                "pattern": {day_names[k]: round(v, 2) for k, v in dow_means.items()},
                "strongest_day": day_names[max(dow_means, key=dow_means.get)],
                "weakest_day": day_names[min(dow_means, key=dow_means.get)],
                "strength": round(dow_variance / total_variance, 3),
            }
        return None
