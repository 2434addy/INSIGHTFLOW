# Skill: Trend Detection

## Overview

Detects, classifies, and quantifies trends in marketing metrics using moving averages, linear regression, and momentum analysis. Provides structured trend data consumed by the Data Analysis Agent and Insight Generation Agent.

## Skill Tier: Atomic

Reusable statistical analysis primitive.

## Capabilities

### 1. Moving Average Analysis

```python
class MovingAverageAnalyzer:
    def compute(
        self,
        timeseries: list[float],
        windows: list[int] = [7, 14, 30],
    ) -> dict[int, list[float]]:
        """Compute simple moving averages for multiple windows."""
        result = {}
        for window in windows:
            result[window] = [
                statistics.mean(timeseries[max(0, i-window+1):i+1])
                for i in range(len(timeseries))
            ]
        return result

    def weighted_moving_average(
        self, timeseries: list[float], window: int = 7
    ) -> list[float]:
        """Recent values weighted more heavily."""
        weights = list(range(1, window + 1))
        total_weight = sum(weights)
        result = []
        for i in range(len(timeseries)):
            start = max(0, i - window + 1)
            segment = timeseries[start:i+1]
            w = weights[-len(segment):]
            result.append(sum(v * wt for v, wt in zip(segment, w)) / sum(w))
        return result
```

### 2. Trend Direction Classification

```python
class TrendClassifier:
    def classify(
        self,
        timeseries: list[float],
        min_data_points: int = 7,
    ) -> TrendResult:
        """
        Classify trend direction and strength.

        Returns:
          direction: accelerating | increasing | stable | decreasing | declining
          strength: 0.0 (flat) to 1.0 (strong trend)
          slope: rate of change per day
          r_squared: goodness of fit (how consistent is the trend)
        """
        if len(timeseries) < min_data_points:
            return TrendResult(direction="insufficient_data", strength=0.0)

        slope, intercept, r_squared = linear_regression(timeseries)

        # Normalize slope relative to mean value
        mean_value = statistics.mean(timeseries)
        if mean_value == 0:
            return TrendResult(direction="stable", strength=0.0)

        normalized_slope = slope / mean_value  # Daily % change

        # Classify direction
        if abs(normalized_slope) < 0.005:  # < 0.5% per day
            direction = "stable"
        elif normalized_slope > 0:
            # Check if accelerating (slope increasing over time)
            first_half_slope = linear_regression(timeseries[:len(timeseries)//2])[0]
            second_half_slope = linear_regression(timeseries[len(timeseries)//2:])[0]
            direction = "accelerating" if second_half_slope > first_half_slope * 1.2 else "increasing"
        else:
            first_half_slope = linear_regression(timeseries[:len(timeseries)//2])[0]
            second_half_slope = linear_regression(timeseries[len(timeseries)//2:])[0]
            direction = "declining" if second_half_slope < first_half_slope * 1.2 else "decreasing"

        # Strength combines magnitude and consistency
        strength = min(1.0, abs(normalized_slope) * 20) * r_squared

        return TrendResult(
            direction=direction,
            strength=round(strength, 2),
            slope=round(slope, 4),
            normalized_slope_pct=round(normalized_slope * 100, 2),
            r_squared=round(r_squared, 3),
        )
```

### 3. Pacing Analysis

```python
class PacingAnalyzer:
    def analyze(
        self,
        actual_spend: list[float],  # Daily spend so far
        budget: float,              # Monthly budget
        days_in_period: int,        # Total days in period
    ) -> PacingResult:
        """
        Determine if spend is on pace to hit budget.

        Returns pacing status: on_track | underspending | overspending
        """
        days_elapsed = len(actual_spend)
        total_spent = sum(actual_spend)
        expected_spent = budget * (days_elapsed / days_in_period)
        pacing_ratio = total_spent / expected_spent if expected_spent > 0 else 0

        if pacing_ratio > 1.15:
            status = "overspending"
        elif pacing_ratio < 0.85:
            status = "underspending"
        else:
            status = "on_track"

        projected_total = (total_spent / days_elapsed) * days_in_period if days_elapsed > 0 else 0

        return PacingResult(
            status=status,
            pacing_ratio=round(pacing_ratio, 2),
            total_spent=total_spent,
            expected_spent=round(expected_spent, 2),
            projected_total=round(projected_total, 2),
            budget=budget,
            days_remaining=days_in_period - days_elapsed,
        )
```

### 4. Seasonality Detection

```python
class SeasonalityDetector:
    def detect_day_of_week_pattern(
        self, timeseries: list[DatedMetric], min_weeks: int = 4
    ) -> SeasonalityResult | None:
        """
        Detect consistent day-of-week patterns.
        Returns normalized day-of-week index (0=Mon, 6=Sun).
        """
        by_dow = group_by_day_of_week(timeseries)
        if len(timeseries) < min_weeks * 7:
            return None

        dow_means = {dow: statistics.mean(vals) for dow, vals in by_dow.items()}
        overall_mean = statistics.mean(m.value for m in timeseries)

        # Check if day-of-week variance is significant
        dow_variance = statistics.variance(dow_means.values())
        total_variance = statistics.variance(m.value for m in timeseries)

        if dow_variance / total_variance > 0.15:  # DoW explains > 15% of variance
            return SeasonalityResult(
                type="day_of_week",
                pattern=dow_means,
                strongest_day=max(dow_means, key=dow_means.get),
                weakest_day=min(dow_means, key=dow_means.get),
                strength=dow_variance / total_variance,
            )
        return None
```

## Output Schema

```json
{
  "metric": "conversions",
  "period": { "start": "2026-02-01", "end": "2026-02-28" },
  "trend": {
    "direction": "increasing",
    "strength": 0.78,
    "slope": 0.43,
    "normalized_slope_pct": 2.1,
    "r_squared": 0.82
  },
  "moving_averages": {
    "7d": 19.4,
    "14d": 18.1,
    "30d": 17.2
  },
  "pacing": {
    "status": "on_track",
    "pacing_ratio": 1.03
  },
  "seasonality": {
    "type": "day_of_week",
    "strongest_day": "Tuesday",
    "weakest_day": "Sunday"
  }
}
```

## Used By

| Agent | Purpose |
|-------|---------|
| Data Analysis Agent | Trend analysis for metrics |
| Anomaly Detection Agent | Baseline trend for anomaly context |
| Insight Generation Agent | Trend narratives |
