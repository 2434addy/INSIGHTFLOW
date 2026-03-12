"""
Semantic Metric Layer — single source of truth for all metric definitions.

Provides metric formulas, platform field mappings, benchmarks, formatting rules,
and directional indicators. Used by nearly every agent in the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MetricUnit(str, Enum):
    COUNT = "count"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    RATIO = "ratio"


class MetricCategory(str, Enum):
    REACH = "reach"
    ENGAGEMENT = "engagement"
    COST = "cost"
    OUTCOME = "outcome"
    EFFICIENCY = "efficiency"
    EFFECTIVENESS = "effectiveness"
    REACH_COST = "reach_cost"
    ROI = "roi"
    VALUE = "value"


@dataclass(frozen=True)
class Benchmark:
    excellent: str | None = None
    good: str | None = None
    average: str | None = None
    poor: str | None = None


@dataclass(frozen=True)
class MetricDefinition:
    id: str
    name: str
    description: str
    unit: MetricUnit
    format: str
    direction: str  # higher_is_better | lower_is_better | neutral
    category: MetricCategory
    aggregation: str = "sum"
    formula: str | None = None
    components: list[str] = field(default_factory=list)
    platform_mapping: dict[str, str | None] = field(default_factory=dict)
    benchmarks: Benchmark = field(default_factory=Benchmark)


# ── Formatting ──────────────────────────────────────────────────


def _compact_number(value: float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(int(value))


FORMATTERS: dict[str, callable] = {
    "integer_comma": lambda v: f"{int(v):,}",
    "currency_2dp": lambda v: f"${v:,.2f}",
    "percentage_2dp": lambda v: f"{v:.2f}%",
    "ratio_2dp": lambda v: f"{v:.2f}x",
    "compact": _compact_number,
}


# ── Metric Catalog ──────────────────────────────────────────────

CORE_METRICS: dict[str, MetricDefinition] = {
    "impressions": MetricDefinition(
        id="impressions",
        name="Impressions",
        description="Number of times an ad was displayed",
        unit=MetricUnit.COUNT,
        format="integer_comma",
        direction="higher_is_better",
        category=MetricCategory.REACH,
        platform_mapping={
            "meta_ads": "impressions",
            "google_ads": "metrics.impressions",
            "ga4": None,
            "shopify": None,
        },
    ),
    "clicks": MetricDefinition(
        id="clicks",
        name="Clicks",
        description="Number of clicks on an ad",
        unit=MetricUnit.COUNT,
        format="integer_comma",
        direction="higher_is_better",
        category=MetricCategory.ENGAGEMENT,
        platform_mapping={
            "meta_ads": "clicks",
            "google_ads": "metrics.clicks",
            "ga4": "sessions",
            "shopify": None,
        },
    ),
    "spend": MetricDefinition(
        id="spend",
        name="Ad Spend",
        description="Total amount spent on advertising",
        unit=MetricUnit.CURRENCY,
        format="currency_2dp",
        direction="neutral",
        category=MetricCategory.COST,
        platform_mapping={
            "meta_ads": "spend",
            "google_ads": "metrics.cost_micros / 1000000",
            "ga4": None,
            "shopify": None,
        },
    ),
    "conversions": MetricDefinition(
        id="conversions",
        name="Conversions",
        description="Number of desired actions completed",
        unit=MetricUnit.COUNT,
        format="integer_comma",
        direction="higher_is_better",
        category=MetricCategory.OUTCOME,
        platform_mapping={
            "meta_ads": "actions[action_type=purchase].value",
            "google_ads": "metrics.conversions",
            "ga4": "conversions",
            "shopify": "orders_count",
        },
    ),
    "conversion_value": MetricDefinition(
        id="conversion_value",
        name="Conversion Value",
        description="Total monetary value of conversions",
        unit=MetricUnit.CURRENCY,
        format="currency_2dp",
        direction="higher_is_better",
        category=MetricCategory.OUTCOME,
        platform_mapping={
            "meta_ads": "action_values[action_type=purchase].value",
            "google_ads": "metrics.conversions_value",
            "ga4": "totalRevenue",
            "shopify": "total_sales",
        },
    ),
}

DERIVED_METRICS: dict[str, MetricDefinition] = {
    "ctr": MetricDefinition(
        id="ctr",
        name="Click-Through Rate",
        description="Percentage of impressions that resulted in a click",
        unit=MetricUnit.PERCENTAGE,
        format="percentage_2dp",
        direction="higher_is_better",
        category=MetricCategory.ENGAGEMENT,
        formula="(clicks / impressions) * 100",
        components=["clicks", "impressions"],
        benchmarks=Benchmark(excellent="> 3.0%", good="1.5% - 3.0%", average="0.5% - 1.5%", poor="< 0.5%"),
    ),
    "cpc": MetricDefinition(
        id="cpc",
        name="Cost Per Click",
        description="Average cost for each click",
        unit=MetricUnit.CURRENCY,
        format="currency_2dp",
        direction="lower_is_better",
        category=MetricCategory.EFFICIENCY,
        formula="spend / clicks",
        components=["spend", "clicks"],
        benchmarks=Benchmark(excellent="< $0.50", good="$0.50 - $1.50", average="$1.50 - $3.00", poor="> $3.00"),
    ),
    "cpa": MetricDefinition(
        id="cpa",
        name="Cost Per Acquisition",
        description="Average cost to acquire one conversion",
        unit=MetricUnit.CURRENCY,
        format="currency_2dp",
        direction="lower_is_better",
        category=MetricCategory.EFFICIENCY,
        formula="spend / conversions",
        components=["spend", "conversions"],
        benchmarks=Benchmark(excellent="< $15", good="$15 - $35", average="$35 - $75", poor="> $75"),
    ),
    "roas": MetricDefinition(
        id="roas",
        name="Return on Ad Spend",
        description="Revenue generated per dollar of ad spend",
        unit=MetricUnit.RATIO,
        format="ratio_2dp",
        direction="higher_is_better",
        category=MetricCategory.ROI,
        formula="conversion_value / spend",
        components=["conversion_value", "spend"],
        benchmarks=Benchmark(excellent="> 5.0x", good="3.0x - 5.0x", average="1.5x - 3.0x", poor="< 1.5x"),
    ),
    "cvr": MetricDefinition(
        id="cvr",
        name="Conversion Rate",
        description="Percentage of clicks that resulted in a conversion",
        unit=MetricUnit.PERCENTAGE,
        format="percentage_2dp",
        direction="higher_is_better",
        category=MetricCategory.EFFECTIVENESS,
        formula="(conversions / clicks) * 100",
        components=["conversions", "clicks"],
    ),
    "cpm": MetricDefinition(
        id="cpm",
        name="Cost Per Mille",
        description="Cost per 1,000 impressions",
        unit=MetricUnit.CURRENCY,
        format="currency_2dp",
        direction="lower_is_better",
        category=MetricCategory.REACH_COST,
        formula="(spend / impressions) * 1000",
        components=["spend", "impressions"],
    ),
    "aov": MetricDefinition(
        id="aov",
        name="Average Order Value",
        description="Average monetary value per conversion",
        unit=MetricUnit.CURRENCY,
        format="currency_2dp",
        direction="higher_is_better",
        category=MetricCategory.VALUE,
        formula="conversion_value / conversions",
        components=["conversion_value", "conversions"],
    ),
}

ALL_METRICS = {**CORE_METRICS, **DERIVED_METRICS}


# ── Service Class ───────────────────────────────────────────────


class SemanticMetricLayer:
    """Single source of truth for all metric definitions."""

    def get_metric(self, metric_id: str) -> MetricDefinition:
        defn = ALL_METRICS.get(metric_id)
        if defn is None:
            raise KeyError(f"Unknown metric: {metric_id}")
        return defn

    def get_formula(self, metric_id: str) -> str | None:
        return self.get_metric(metric_id).formula

    def get_platform_field(self, metric_id: str, platform: str) -> str | None:
        return self.get_metric(metric_id).platform_mapping.get(platform)

    def format_value(self, metric_id: str, value: float | None) -> str:
        if value is None:
            return "N/A"
        fmt = self.get_metric(metric_id).format
        formatter = FORMATTERS.get(fmt)
        if formatter is None:
            return str(value)
        return formatter(value)

    def get_direction(self, metric_id: str) -> str:
        return self.get_metric(metric_id).direction

    def get_benchmarks(self, metric_id: str) -> Benchmark:
        return self.get_metric(metric_id).benchmarks

    def list_metrics(self, category: MetricCategory | None = None) -> list[MetricDefinition]:
        metrics = list(ALL_METRICS.values())
        if category is not None:
            metrics = [m for m in metrics if m.category == category]
        return metrics

    def is_derived(self, metric_id: str) -> bool:
        return metric_id in DERIVED_METRICS
