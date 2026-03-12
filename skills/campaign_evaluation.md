# Skill: Campaign Evaluation

## Overview

Evaluates and scores individual campaigns and ad groups based on configurable performance criteria. Produces tier classifications, efficiency rankings, and budget allocation assessments.

## Skill Tier: Atomic

Reusable evaluation logic used by the Performance Segmentation Agent and Recommendation Agent.

## Capabilities

### 1. Tier Classification

```python
class TierClassifier:
    TIERS = {
        "star":           {"label": "★ Star",          "min_percentile": 90},
        "strong":         {"label": "▲ Strong",        "min_percentile": 60},
        "average":        {"label": "● Average",       "min_percentile": 30},
        "underperformer": {"label": "▼ Underperformer","min_percentile": 10},
        "waster":         {"label": "✕ Waster",        "min_percentile": 0},
    }

    def classify(
        self,
        campaigns: list[CampaignMetrics],
        scorer: EfficiencyScorer,
        min_spend: float = 10.0,
    ) -> dict[str, list[TieredCampaign]]:
        """
        Score all campaigns and classify into tiers.
        Campaigns below min_spend are excluded (insufficient data).
        """
        eligible = [c for c in campaigns if c.spend >= min_spend]
        scores = [(c, scorer.score(c)) for c in eligible]
        scores.sort(key=lambda x: x[1], reverse=True)

        percentiles = compute_percentiles(scores)
        result = {tier: [] for tier in self.TIERS}

        for campaign, score in scores:
            pct = percentiles[campaign.id]
            tier = self._get_tier(pct)
            result[tier].append(TieredCampaign(
                campaign=campaign,
                efficiency_score=score,
                percentile=pct,
                tier=tier,
            ))
        return result
```

### 2. Budget Allocation Assessment

```python
class BudgetAssessor:
    def assess(
        self,
        tiered_campaigns: dict[str, list[TieredCampaign]],
        total_spend: float,
    ) -> BudgetAssessment:
        """
        Analyze how budget is distributed across performance tiers.
        Identify misallocation (too much on wasters, too little on stars).
        """
        tier_spends = {}
        for tier, campaigns in tiered_campaigns.items():
            tier_spend = sum(c.campaign.spend for c in campaigns)
            tier_spends[tier] = {
                "absolute": tier_spend,
                "share_pct": (tier_spend / total_spend * 100) if total_spend > 0 else 0,
                "campaign_count": len(campaigns),
            }

        # Calculate reallocation potential
        waster_spend = tier_spends.get("waster", {}).get("absolute", 0)
        star_avg_roas = statistics.mean(
            c.campaign.roas for c in tiered_campaigns.get("star", [])
        ) if tiered_campaigns.get("star") else 0

        return BudgetAssessment(
            tier_distribution=tier_spends,
            reallocation_potential=waster_spend,
            is_well_allocated=tier_spends.get("waster", {}).get("share_pct", 0) < 5,
            estimated_impact=self._estimate_reallocation_impact(
                waster_spend, star_avg_roas
            ),
        )
```

### 3. Diminishing Returns Detection

```python
class DiminishingReturnsDetector:
    def detect(
        self,
        campaign_history: list[DailyMetrics],
        lookback_days: int = 30,
    ) -> DiminishingReturnsResult | None:
        """
        Detect if a campaign is hitting efficiency ceilings.

        Signals:
        - CPA increasing while spend stable or increasing
        - ROAS decreasing over time
        - Frequency > 3x (ad fatigue)
        - CVR declining while impressions growing
        """
        if len(campaign_history) < lookback_days:
            return None

        recent = campaign_history[-lookback_days:]
        cpa_trend = compute_trend([d.cpa for d in recent if d.cpa])
        spend_trend = compute_trend([d.spend for d in recent])
        freq_trend = compute_trend([d.frequency for d in recent if d.frequency])

        signals = []
        if cpa_trend.direction in ("increasing", "accelerating") and \
           spend_trend.direction in ("stable", "increasing"):
            signals.append("CPA rising while spend held constant")

        avg_frequency = statistics.mean([d.frequency for d in recent if d.frequency])
        if avg_frequency > 3.0:
            signals.append(f"High frequency ({avg_frequency:.1f}x) indicates ad fatigue")

        if signals:
            return DiminishingReturnsResult(
                campaign_id=recent[0].campaign_id,
                signals=signals,
                severity="high" if len(signals) > 1 else "medium",
                recommendation="Refresh creative, expand audience, or reduce budget",
            )
        return None
```

### 4. Cross-Platform Comparison

```python
class PlatformComparator:
    def compare(
        self,
        platform_metrics: dict[str, SummaryMetrics],
    ) -> PlatformComparison:
        """
        Compare performance across platforms on key metrics.
        Returns relative efficiency rankings.
        """
        rankings = {}
        for metric in ["roas", "cpa", "ctr", "cvr"]:
            sorted_platforms = sorted(
                platform_metrics.items(),
                key=lambda x: getattr(x[1], metric) or 0,
                reverse=(metric != "cpa"),  # Lower CPA is better
            )
            rankings[metric] = [p[0] for p in sorted_platforms]

        return PlatformComparison(
            metrics=platform_metrics,
            rankings=rankings,
            most_efficient=rankings["roas"][0],
            highest_volume=max(platform_metrics, key=lambda p: platform_metrics[p].conversions),
        )
```

## Used By

| Agent | Purpose |
|-------|---------|
| Performance Segmentation Agent | Tier classification, budget assessment |
| Recommendation Agent | Optimization opportunities |
| Data Analysis Agent | Campaign ranking |
