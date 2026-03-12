# Skill: Anomaly Detection

## Overview

Provides statistical anomaly detection algorithms for marketing metrics. Detects outliers, pattern breaks, and correlation anomalies using Z-score, IQR, and contextual analysis methods.

## Skill Tier: Atomic

Core statistical detection algorithms used by the Anomaly Detection Agent.

## Algorithms

### 1. Z-Score Detection

```python
class ZScoreDetector:
    def detect(
        self,
        timeseries: list[float],
        threshold: float = 2.5,
        rolling_window: int = 30,
    ) -> list[AnomalyPoint]:
        """
        Detect points where |z-score| > threshold using a rolling baseline.

        Rolling window adapts to changing baselines
        (e.g., gradual spend increases don't trigger false positives).
        """
        anomalies = []
        for i in range(rolling_window, len(timeseries)):
            window = timeseries[i - rolling_window:i]
            mean = statistics.mean(window)
            std = statistics.stdev(window) if len(window) > 1 else 0

            if std == 0:
                continue

            z_score = (timeseries[i] - mean) / std

            if abs(z_score) > threshold:
                anomalies.append(AnomalyPoint(
                    index=i,
                    value=timeseries[i],
                    expected=round(mean, 2),
                    z_score=round(z_score, 2),
                    type="spike" if z_score > 0 else "drop",
                    deviation_pct=round(((timeseries[i] - mean) / mean) * 100, 1),
                ))
        return anomalies
```

### 2. IQR (Interquartile Range) Detection

```python
class IQRDetector:
    def detect(
        self,
        timeseries: list[float],
        multiplier: float = 1.5,
    ) -> list[AnomalyPoint]:
        """
        Detect outliers using IQR method. More robust than Z-score
        for non-normal distributions (common in marketing data).

        Outlier if: value < Q1 - multiplier*IQR or value > Q3 + multiplier*IQR
        """
        q1 = percentile(timeseries, 25)
        q3 = percentile(timeseries, 75)
        iqr = q3 - q1
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr

        return [
            AnomalyPoint(index=i, value=v, type="spike" if v > upper_bound else "drop")
            for i, v in enumerate(timeseries)
            if v < lower_bound or v > upper_bound
        ]
```

### 3. Contextual Anomaly Detection

```python
class ContextualDetector:
    def detect_by_day_of_week(
        self,
        timeseries: list[DatedMetric],
        threshold: float = 2.0,
    ) -> list[AnomalyPoint]:
        """
        Detect values that are unusual for their specific day of week.
        Monday spend is normally lower than Friday — that's expected.
        But if Monday spend is 3x the normal Monday level, flag it.
        """
        by_dow = group_by_day_of_week(timeseries)
        anomalies = []
        for point in timeseries:
            dow = point.date.weekday()
            dow_values = by_dow[dow]
            dow_mean = statistics.mean(dow_values)
            dow_std = statistics.stdev(dow_values) if len(dow_values) > 1 else 0

            if dow_std > 0:
                z = (point.value - dow_mean) / dow_std
                if abs(z) > threshold:
                    anomalies.append(AnomalyPoint(
                        index=timeseries.index(point),
                        value=point.value,
                        expected=round(dow_mean, 2),
                        z_score=round(z, 2),
                        context=f"Unusual for {point.date.strftime('%A')}",
                    ))
        return anomalies
```

### 4. Correlation Break Detection

```python
class CorrelationBreakDetector:
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
        """
        Detect when normally correlated metrics diverge.
        Uses a sliding window to compare recent correlation to historical.
        """
        anomalies = []
        for (m1, m2), expected in self.EXPECTED_CORRELATIONS.items():
            if m1 not in metrics or m2 not in metrics:
                continue

            historical_r = correlation(metrics[m1][:-window], metrics[m2][:-window])
            recent_r = correlation(metrics[m1][-window:], metrics[m2][-window:])

            if abs(historical_r - recent_r) > 0.4:
                anomalies.append(CorrelationAnomaly(
                    metric_pair=(m1, m2),
                    historical_correlation=round(historical_r, 2),
                    recent_correlation=round(recent_r, 2),
                    significance="high" if abs(historical_r - recent_r) > 0.6 else "medium",
                ))
        return anomalies
```

### 5. Missing Data Detection

```python
class MissingDataDetector:
    def detect(
        self,
        dates_with_data: list[date],
        expected_start: date,
        expected_end: date,
    ) -> list[date]:
        """Return dates that should have data but don't."""
        expected_dates = set(date_range(expected_start, expected_end))
        actual_dates = set(dates_with_data)
        return sorted(expected_dates - actual_dates)
```

## Severity Classification

```python
def classify_severity(anomaly: AnomalyPoint, metric_id: str) -> str:
    """
    Classify anomaly severity based on z-score and metric importance.

    Revenue-impacting metrics (spend, conversions, ROAS) get higher severity
    at lower thresholds than volume metrics (impressions, clicks).
    """
    REVENUE_METRICS = {"spend", "conversions", "conversion_value", "roas", "cpa"}

    z = abs(anomaly.z_score)
    is_revenue = metric_id in REVENUE_METRICS

    if z > 4.0 or (is_revenue and z > 3.0):
        return "critical"
    elif z > 3.0 or (is_revenue and z > 2.5):
        return "high"
    elif z > 2.5:
        return "medium"
    else:
        return "low"
```

## Used By

| Agent | Purpose |
|-------|---------|
| Anomaly Detection Agent | Core detection algorithms |
| Data Analysis Agent | Outlier flagging in analysis |
| Insight Generation Agent | Anomaly context for narratives |
