# Skill: Semantic Metric Layer

## Overview

A structured catalog defining every marketing metric's formula, unit, direction (higher/lower is better), benchmark thresholds, platform-specific field mappings, and formatting rules. Serves as the single source of truth for data normalization and AI grounding.

## Skill Tier: Atomic

This is a foundational skill used by nearly every agent in the pipeline. It prevents metric definition inconsistencies and gives the AI precise definitions rather than letting it guess.

## Metric Catalog

### Core Metrics

```yaml
metrics:
  impressions:
    id: impressions
    name: Impressions
    description: Number of times an ad was displayed
    unit: count
    format: "integer_comma"  # 1,234,567
    direction: higher_is_better
    category: reach
    aggregation: sum
    platform_mapping:
      meta_ads: impressions
      google_ads: metrics.impressions
      ga4: null  # Not applicable
      shopify: null
    benchmarks:
      good: null  # Context-dependent
      concern: null

  clicks:
    id: clicks
    name: Clicks
    description: Number of clicks on an ad
    unit: count
    format: "integer_comma"
    direction: higher_is_better
    category: engagement
    aggregation: sum
    platform_mapping:
      meta_ads: clicks
      google_ads: metrics.clicks
      ga4: sessions  # Closest equivalent
      shopify: null

  spend:
    id: spend
    name: Ad Spend
    description: Total amount spent on advertising
    unit: currency
    format: "currency_2dp"  # $1,234.56
    direction: neutral  # Context-dependent
    category: cost
    aggregation: sum
    platform_mapping:
      meta_ads: spend
      google_ads: "metrics.cost_micros / 1000000"
      ga4: null
      shopify: null

  conversions:
    id: conversions
    name: Conversions
    description: Number of desired actions completed (purchases, signups, etc.)
    unit: count
    format: "integer_comma"
    direction: higher_is_better
    category: outcome
    aggregation: sum
    platform_mapping:
      meta_ads: "actions[action_type=purchase].value"
      google_ads: metrics.conversions
      ga4: conversions
      shopify: orders_count

  conversion_value:
    id: conversion_value
    name: Conversion Value
    description: Total monetary value of conversions
    unit: currency
    format: "currency_2dp"
    direction: higher_is_better
    category: outcome
    aggregation: sum
    platform_mapping:
      meta_ads: "action_values[action_type=purchase].value"
      google_ads: metrics.conversions_value
      ga4: totalRevenue
      shopify: total_sales
```

### Derived Metrics

```yaml
derived_metrics:
  ctr:
    id: ctr
    name: Click-Through Rate
    description: Percentage of impressions that resulted in a click
    formula: "(clicks / impressions) * 100"
    unit: percentage
    format: "percentage_2dp"  # 2.45%
    direction: higher_is_better
    category: engagement
    components: [clicks, impressions]
    benchmarks:
      excellent: "> 3.0%"
      good: "1.5% - 3.0%"
      average: "0.5% - 1.5%"
      poor: "< 0.5%"
    division_by_zero: null  # Return null if impressions = 0

  cpc:
    id: cpc
    name: Cost Per Click
    description: Average cost for each click
    formula: "spend / clicks"
    unit: currency
    format: "currency_2dp"
    direction: lower_is_better
    category: efficiency
    components: [spend, clicks]
    benchmarks:
      excellent: "< $0.50"
      good: "$0.50 - $1.50"
      average: "$1.50 - $3.00"
      poor: "> $3.00"
    division_by_zero: null

  cpa:
    id: cpa
    name: Cost Per Acquisition
    description: Average cost to acquire one conversion
    formula: "spend / conversions"
    unit: currency
    format: "currency_2dp"
    direction: lower_is_better
    category: efficiency
    components: [spend, conversions]
    benchmarks:
      excellent: "< $15"
      good: "$15 - $35"
      average: "$35 - $75"
      poor: "> $75"
    division_by_zero: null

  roas:
    id: roas
    name: Return on Ad Spend
    description: Revenue generated per dollar of ad spend
    formula: "conversion_value / spend"
    unit: ratio
    format: "ratio_2dp"  # 4.50x
    direction: higher_is_better
    category: roi
    components: [conversion_value, spend]
    benchmarks:
      excellent: "> 5.0x"
      good: "3.0x - 5.0x"
      average: "1.5x - 3.0x"
      poor: "< 1.5x"
      breakeven: "1.0x"
    division_by_zero: null

  cvr:
    id: cvr
    name: Conversion Rate
    description: Percentage of clicks that resulted in a conversion
    formula: "(conversions / clicks) * 100"
    unit: percentage
    format: "percentage_2dp"
    direction: higher_is_better
    category: effectiveness
    components: [conversions, clicks]
    division_by_zero: null

  cpm:
    id: cpm
    name: Cost Per Mille
    description: Cost per 1,000 impressions
    formula: "(spend / impressions) * 1000"
    unit: currency
    format: "currency_2dp"
    direction: lower_is_better
    category: reach_cost
    components: [spend, impressions]
    division_by_zero: null

  aov:
    id: aov
    name: Average Order Value
    description: Average monetary value per conversion
    formula: "conversion_value / conversions"
    unit: currency
    format: "currency_2dp"
    direction: higher_is_better
    category: value
    components: [conversion_value, conversions]
    division_by_zero: null
```

## Formatting Rules

```python
FORMATTERS = {
    "integer_comma": lambda v: f"{int(v):,}",                    # 1,234,567
    "currency_2dp": lambda v, sym="$": f"{sym}{v:,.2f}",         # $1,234.56
    "percentage_2dp": lambda v: f"{v:.2f}%",                      # 2.45%
    "ratio_2dp": lambda v: f"{v:.2f}x",                           # 4.50x
    "compact": lambda v: compact_number(v),                       # 1.2M, 45.3K
}

def compact_number(value: float) -> str:
    if value >= 1_000_000: return f"{value/1_000_000:.1f}M"
    if value >= 1_000: return f"{value/1_000:.1f}K"
    return str(int(value))
```

## Usage by Agents

| Agent | Usage |
|-------|-------|
| Data Normalization Agent | Platform field mappings, formula definitions |
| Data Analysis Agent | Benchmark thresholds, metric directions |
| Anomaly Detection Agent | Expected ranges for anomaly classification |
| Insight Generation Agent | AI grounding — precise metric definitions |
| Validation Agent | Verify calculations match formulas |
| Visualization Agent | Formatting rules for chart labels |

## Interface

```python
class SemanticMetricLayer:
    def get_metric(self, metric_id: str) -> MetricDefinition: ...
    def get_formula(self, metric_id: str) -> str: ...
    def get_platform_field(self, metric_id: str, platform: str) -> str | None: ...
    def format_value(self, metric_id: str, value: float) -> str: ...
    def get_benchmark(self, metric_id: str, level: str) -> str | None: ...
    def get_direction(self, metric_id: str) -> str: ...
    def list_metrics(self, category: str = None) -> list[MetricDefinition]: ...
```
