"""
KPI Computation skill — derived metrics, aggregation, period comparison.

Handles safe division, null propagation, and multi-dimensional aggregation.
"""

from __future__ import annotations

from collections import defaultdict

from app.pipeline.schemas import (
    MetricRecord,
    PeriodComparison,
    SummaryMetrics,
)


def safe_divide(num: float | None, den: float | None) -> float | None:
    """Safely divide two values, returning None on zero or missing input."""
    if num is None or den is None or den == 0:
        return None
    return num / den


def pct_change(old: float | None, new: float | None) -> float | None:
    """Calculate percentage change from old to new."""
    if old is None or new is None or old == 0:
        return None
    return ((new - old) / abs(old)) * 100


class KPIComputer:
    """Computes all derived metrics for metric records."""

    def compute_derived(self, record: MetricRecord) -> MetricRecord:
        """Compute all derived metrics for a single record in-place."""
        record.ctr = _mul100(safe_divide(record.clicks, record.impressions))
        record.cpc = safe_divide(record.spend, record.clicks)
        record.cpa = safe_divide(record.spend, record.conversions)
        record.roas = safe_divide(record.conversion_value, record.spend)
        record.cvr = _mul100(safe_divide(record.conversions, record.clicks))
        record.cpm = _mul1000(safe_divide(record.spend, record.impressions))
        record.aov = safe_divide(record.conversion_value, record.conversions)
        return record

    def compute_all(self, records: list[MetricRecord]) -> list[MetricRecord]:
        """Compute derived metrics for a batch of records."""
        return [self.compute_derived(r) for r in records]


class Aggregator:
    """Aggregates metric records by arbitrary dimensions."""

    def aggregate_summary(self, records: list[MetricRecord]) -> SummaryMetrics:
        """Compute a single summary across all records."""
        if not records:
            return SummaryMetrics()

        total_spend = sum(r.spend for r in records)
        total_impressions = sum(r.impressions for r in records)
        total_clicks = sum(r.clicks for r in records)
        total_conversions = sum(r.conversions for r in records)
        total_value = sum(r.conversion_value for r in records)

        return SummaryMetrics(
            spend=total_spend,
            impressions=total_impressions,
            clicks=total_clicks,
            conversions=total_conversions,
            conversion_value=total_value,
            ctr=_mul100(safe_divide(total_clicks, total_impressions)),
            cpc=safe_divide(total_spend, total_clicks),
            cpa=safe_divide(total_spend, total_conversions),
            roas=safe_divide(total_value, total_spend),
            cvr=_mul100(safe_divide(total_conversions, total_clicks)),
            cpm=_mul1000(safe_divide(total_spend, total_impressions)),
            aov=safe_divide(total_value, total_conversions),
        )

    def aggregate_by(
        self, records: list[MetricRecord], key: str
    ) -> dict[str, SummaryMetrics]:
        """Group records by a field and aggregate each group."""
        groups: dict[str, list[MetricRecord]] = defaultdict(list)
        for r in records:
            group_value = str(getattr(r, key, "unknown"))
            groups[group_value].append(r)

        return {k: self.aggregate_summary(v) for k, v in groups.items()}


class PeriodComparer:
    """Computes period-over-period changes."""

    def compare(
        self, current: SummaryMetrics, previous: SummaryMetrics
    ) -> PeriodComparison:
        return PeriodComparison(
            spend_delta=current.spend - previous.spend,
            spend_change_pct=pct_change(previous.spend, current.spend),
            impressions_delta=current.impressions - previous.impressions,
            impressions_change_pct=pct_change(previous.impressions, current.impressions),
            clicks_delta=current.clicks - previous.clicks,
            clicks_change_pct=pct_change(previous.clicks, current.clicks),
            conversions_delta=current.conversions - previous.conversions,
            conversions_change_pct=pct_change(previous.conversions, current.conversions),
            conversion_value_delta=current.conversion_value - previous.conversion_value,
            conversion_value_change_pct=pct_change(
                previous.conversion_value, current.conversion_value
            ),
            roas_delta=_safe_sub(current.roas, previous.roas),
            roas_change_pct=pct_change(previous.roas, current.roas),
            cpa_delta=_safe_sub(current.cpa, previous.cpa),
            cpa_change_pct=pct_change(previous.cpa, current.cpa),
            ctr_delta=_safe_sub(current.ctr, previous.ctr),
            ctr_change_pct=pct_change(previous.ctr, current.ctr),
        )


class EfficiencyScorer:
    """Computes composite efficiency score (0.0 to 1.0) for campaigns."""

    DEFAULT_WEIGHTS = {"roas": 0.35, "cpa": 0.30, "cvr": 0.20, "volume": 0.15}

    def score(
        self,
        roas: float | None,
        cpa: float | None,
        cvr: float | None,
        conversions: int,
        benchmarks: dict[str, tuple[float, float]],
        weights: dict[str, float] | None = None,
    ) -> float:
        """
        Compute composite efficiency score.

        benchmarks: dict mapping metric name to (p25, p75) tuple.
        """
        w = weights or self.DEFAULT_WEIGHTS

        roas_score = self._normalize(roas or 0, *benchmarks.get("roas", (1.0, 5.0)))
        cpa_score = 1.0 - self._normalize(cpa or 0, *benchmarks.get("cpa", (15.0, 75.0)))
        cvr_score = self._normalize(cvr or 0, *benchmarks.get("cvr", (1.0, 5.0)))
        volume_score = self._normalize(
            conversions, 0, benchmarks.get("volume", (0, 100))[1]
        )

        return (
            w["roas"] * roas_score
            + w["cpa"] * cpa_score
            + w["cvr"] * cvr_score
            + w["volume"] * volume_score
        )

    @staticmethod
    def _normalize(value: float, low: float, high: float) -> float:
        if high == low:
            return 0.5
        return max(0.0, min(1.0, (value - low) / (high - low)))


# ── Helpers ─────────────────────────────────────────────────────


def _mul100(v: float | None) -> float | None:
    return v * 100 if v is not None else None


def _mul1000(v: float | None) -> float | None:
    return v * 1000 if v is not None else None


def _safe_sub(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return a - b
