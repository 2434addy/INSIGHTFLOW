# Skill: KPI Computation

## Overview

Provides the computation engine for all marketing KPIs — both core metrics (aggregation) and derived metrics (formulas). Handles safe division, null propagation, and multi-dimensional aggregation.

## Skill Tier: Atomic

Reusable primitive used by the Data Normalization Agent, Data Analysis Agent, and Performance Segmentation Agent.

## Capabilities

### 1. Derived Metric Computation

```python
class KPIComputer:
    def compute_all(self, record: MetricRecord) -> MetricRecord:
        """Compute all derived metrics for a single record."""
        record.ctr = self.safe_divide(record.clicks, record.impressions) * 100
        record.cpc = self.safe_divide(record.spend, record.clicks)
        record.cpa = self.safe_divide(record.spend, record.conversions)
        record.roas = self.safe_divide(record.conversion_value, record.spend)
        record.cvr = self.safe_divide(record.conversions, record.clicks) * 100
        record.cpm = self.safe_divide(record.spend, record.impressions) * 1000
        record.aov = self.safe_divide(record.conversion_value, record.conversions)
        return record

    def safe_divide(self, num: float | None, den: float | None) -> float | None:
        if num is None or den is None or den == 0:
            return None
        return num / den
```

### 2. Multi-Dimensional Aggregation

```python
class Aggregator:
    def aggregate(
        self,
        records: list[MetricRecord],
        group_by: list[str],  # e.g., ["platform", "date"]
        metrics: list[str],   # e.g., ["spend", "conversions"]
    ) -> list[AggregatedRecord]:
        """
        Group records by dimensions and aggregate metrics.
        SUM for: spend, impressions, clicks, conversions, conversion_value
        Derived metrics are recomputed from aggregated totals (not averaged).
        """

    def aggregate_summary(self, records: list[MetricRecord]) -> SummaryMetrics:
        """Compute a single summary across all records."""
        total_spend = sum(r.spend for r in records)
        total_conversions = sum(r.conversions for r in records)
        total_value = sum(r.conversion_value for r in records)
        total_impressions = sum(r.impressions for r in records)
        total_clicks = sum(r.clicks for r in records)

        return SummaryMetrics(
            spend=total_spend,
            impressions=total_impressions,
            clicks=total_clicks,
            conversions=total_conversions,
            conversion_value=total_value,
            ctr=safe_divide(total_clicks, total_impressions) * 100,
            cpc=safe_divide(total_spend, total_clicks),
            cpa=safe_divide(total_spend, total_conversions),
            roas=safe_divide(total_value, total_spend),
            cvr=safe_divide(total_conversions, total_clicks) * 100,
            cpm=safe_divide(total_spend, total_impressions) * 1000,
            aov=safe_divide(total_value, total_conversions),
        )
```

### 3. Period-over-Period Calculation

```python
class PeriodComparison:
    def compare(
        self, current: SummaryMetrics, previous: SummaryMetrics
    ) -> ComparisonResult:
        """Calculate absolute and percentage changes between periods."""
        return ComparisonResult(
            spend_delta=current.spend - previous.spend,
            spend_change_pct=self.pct_change(previous.spend, current.spend),
            conversions_delta=current.conversions - previous.conversions,
            conversions_change_pct=self.pct_change(previous.conversions, current.conversions),
            roas_delta=current.roas - previous.roas if current.roas and previous.roas else None,
            roas_change_pct=self.pct_change(previous.roas, current.roas),
            cpa_delta=current.cpa - previous.cpa if current.cpa and previous.cpa else None,
            cpa_change_pct=self.pct_change(previous.cpa, current.cpa),
        )

    def pct_change(self, old: float | None, new: float | None) -> float | None:
        if old is None or new is None or old == 0:
            return None
        return ((new - old) / abs(old)) * 100
```

### 4. Composite Scoring

```python
class EfficiencyScorer:
    def score(
        self,
        campaign: CampaignMetrics,
        benchmarks: Benchmarks,
        weights: dict[str, float] = None,
    ) -> float:
        """
        Compute composite efficiency score (0.0 to 1.0).
        Default weights: ROAS 35%, CPA 30%, CVR 20%, Volume 15%
        """
        weights = weights or {"roas": 0.35, "cpa": 0.30, "cvr": 0.20, "volume": 0.15}

        roas_score = self.normalize(campaign.roas, benchmarks.roas_p25, benchmarks.roas_p75)
        cpa_score = 1.0 - self.normalize(campaign.cpa, benchmarks.cpa_p25, benchmarks.cpa_p75)
        cvr_score = self.normalize(campaign.cvr, benchmarks.cvr_p25, benchmarks.cvr_p75)
        volume_score = self.normalize(campaign.conversions, 0, benchmarks.conversions_p90)

        return (
            weights["roas"] * roas_score +
            weights["cpa"] * cpa_score +
            weights["cvr"] * cvr_score +
            weights["volume"] * volume_score
        )

    def normalize(self, value: float, low: float, high: float) -> float:
        if high == low:
            return 0.5
        return max(0.0, min(1.0, (value - low) / (high - low)))
```

## Used By

| Agent | Purpose |
|-------|---------|
| Data Normalization Agent | Derived metric computation on raw data |
| Data Analysis Agent | Aggregation, comparison, trend metrics |
| Performance Segmentation Agent | Efficiency scoring, ranking |
| Validation Agent | Verify calculations in AI output |
