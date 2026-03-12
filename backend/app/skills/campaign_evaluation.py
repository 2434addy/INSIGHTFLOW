"""
Campaign Evaluation skill — tier classification, budget assessment, comparisons.

Evaluates and scores campaigns based on configurable performance criteria.
"""

from __future__ import annotations

import statistics

from app.pipeline.schemas import (
    BudgetAssessment,
    CampaignTier,
    MetricRecord,
    SummaryMetrics,
    TieredCampaign,
)
from app.skills.kpi_computation import Aggregator, EfficiencyScorer, safe_divide


TIER_THRESHOLDS = {
    CampaignTier.STAR: 90,
    CampaignTier.STRONG: 60,
    CampaignTier.AVERAGE: 30,
    CampaignTier.UNDERPERFORMER: 10,
    CampaignTier.WASTER: 0,
}


class TierClassifier:
    """Scores all campaigns and classifies them into performance tiers."""

    def __init__(self, min_spend: float = 10.0):
        self._min_spend = min_spend
        self._scorer = EfficiencyScorer()
        self._aggregator = Aggregator()

    def classify(
        self,
        records: list[MetricRecord],
    ) -> dict[str, list[TieredCampaign]]:
        """
        Group records by campaign, compute efficiency scores,
        and assign performance tiers.
        """
        # Aggregate by campaign
        campaign_groups: dict[str, list[MetricRecord]] = {}
        for r in records:
            key = str(r.campaign_id)
            campaign_groups.setdefault(key, []).append(r)

        # Score each campaign
        scored: list[tuple[MetricRecord, SummaryMetrics, float]] = []
        benchmarks = self._compute_benchmarks(records)

        for cid, group in campaign_groups.items():
            summary = self._aggregator.aggregate_summary(group)
            if summary.spend < self._min_spend:
                continue
            score = self._scorer.score(
                roas=summary.roas,
                cpa=summary.cpa,
                cvr=summary.cvr,
                conversions=summary.conversions,
                benchmarks=benchmarks,
            )
            scored.append((group[0], summary, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[2], reverse=True)

        # Assign percentiles
        n = len(scored)
        result: dict[str, list[TieredCampaign]] = {t.value: [] for t in CampaignTier}

        for rank, (rec, summary, score) in enumerate(scored):
            percentile = ((n - rank) / n) * 100 if n > 0 else 50
            tier = self._get_tier(percentile)

            tc = TieredCampaign(
                campaign_id=rec.campaign_id,
                campaign_name=rec.campaign_name,
                platform=rec.platform,
                tier=tier,
                efficiency_score=round(score, 3),
                percentile=round(percentile, 1),
                spend=summary.spend,
                roas=summary.roas,
                cpa=summary.cpa,
                conversions=summary.conversions,
            )
            result[tier.value].append(tc)

        return result

    @staticmethod
    def _get_tier(percentile: float) -> CampaignTier:
        for tier, threshold in TIER_THRESHOLDS.items():
            if percentile >= threshold:
                return tier
        return CampaignTier.WASTER

    @staticmethod
    def _compute_benchmarks(records: list[MetricRecord]) -> dict[str, tuple[float, float]]:
        """Compute p25/p75 benchmarks from the dataset for scoring."""
        aggregator = Aggregator()
        campaign_groups: dict[str, list[MetricRecord]] = {}
        for r in records:
            campaign_groups.setdefault(str(r.campaign_id), []).append(r)

        summaries = [aggregator.aggregate_summary(g) for g in campaign_groups.values()]

        roas_vals = sorted(s.roas for s in summaries if s.roas is not None)
        cpa_vals = sorted(s.cpa for s in summaries if s.cpa is not None)
        cvr_vals = sorted(s.cvr for s in summaries if s.cvr is not None)
        conv_vals = sorted(s.conversions for s in summaries)

        return {
            "roas": _percentile_pair(roas_vals),
            "cpa": _percentile_pair(cpa_vals),
            "cvr": _percentile_pair(cvr_vals),
            "volume": (0, _percentile_val(conv_vals, 90)),
        }


class BudgetAssessor:
    """Analyzes budget distribution across performance tiers."""

    def assess(
        self,
        tiered_campaigns: dict[str, list[TieredCampaign]],
    ) -> BudgetAssessment:
        total_spend = sum(
            c.spend
            for campaigns in tiered_campaigns.values()
            for c in campaigns
        )

        tier_distribution: dict[str, dict] = {}
        for tier_name, campaigns in tiered_campaigns.items():
            tier_spend = sum(c.spend for c in campaigns)
            tier_distribution[tier_name] = {
                "absolute": round(tier_spend, 2),
                "share_pct": round(tier_spend / total_spend * 100, 1) if total_spend > 0 else 0,
                "campaign_count": len(campaigns),
            }

        waster_spend = tier_distribution.get("waster", {}).get("absolute", 0)
        waster_share = tier_distribution.get("waster", {}).get("share_pct", 0)

        star_campaigns = tiered_campaigns.get("star", [])
        star_roas_vals = [c.roas for c in star_campaigns if c.roas]
        star_avg_roas = statistics.mean(star_roas_vals) if star_roas_vals else 0

        estimated_impact = ""
        if waster_spend > 0 and star_avg_roas > 0:
            potential_revenue = waster_spend * star_avg_roas
            estimated_impact = (
                f"Reallocating ${waster_spend:,.0f} from waster campaigns to "
                f"star performers could generate ~${potential_revenue:,.0f} in revenue"
            )

        return BudgetAssessment(
            tier_distribution=tier_distribution,
            reallocation_potential=waster_spend,
            is_well_allocated=waster_share < 5,
            estimated_impact=estimated_impact,
        )


class PlatformComparator:
    """Compares performance across platforms."""

    def compare(
        self,
        platform_summaries: dict[str, SummaryMetrics],
    ) -> dict[str, dict]:
        rankings: dict[str, list[str]] = {}
        for metric in ["roas", "cpa", "ctr", "cvr"]:
            reverse = metric != "cpa"  # Lower CPA is better
            sorted_platforms = sorted(
                platform_summaries.items(),
                key=lambda x: getattr(x[1], metric) or 0,
                reverse=reverse,
            )
            rankings[metric] = [p[0] for p in sorted_platforms]

        most_efficient = rankings.get("roas", [""])[0]
        highest_volume = max(
            platform_summaries,
            key=lambda p: platform_summaries[p].conversions,
            default="",
        )

        return {
            "rankings": rankings,
            "most_efficient": most_efficient,
            "highest_volume": highest_volume,
        }


def _percentile_pair(vals: list[float]) -> tuple[float, float]:
    """Return (p25, p75) for a sorted list."""
    if not vals:
        return (0.0, 1.0)
    return (_percentile_val(vals, 25), _percentile_val(vals, 75))


def _percentile_val(vals: list[float], pct: int) -> float:
    """Return the value at the given percentile from a sorted list."""
    if not vals:
        return 0.0
    idx = int(len(vals) * pct / 100)
    idx = min(idx, len(vals) - 1)
    return vals[idx]
