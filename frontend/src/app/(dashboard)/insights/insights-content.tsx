"use client";

import { InsightCard } from "@/components/reports/insight-card";
import { RecommendationCard } from "@/components/reports/recommendation-card";
import { PageHeader } from "@/components/common/page-header";
import { Topbar } from "@/components/layout/topbar";
import { cn } from "@/lib/utils";
import type { Insight, Recommendation } from "@/types/api";
import { useState } from "react";

const DEMO_INSIGHTS: Insight[] = [
  {
    id: "1",
    category: "performance",
    sentiment: "positive",
    priority: 1,
    headline: "Conversions up 12.5% month-over-month",
    detail:
      "Total conversions increased from 1,618 to 1,820 compared to the previous period, driven primarily by Meta retargeting campaigns which saw a 23% lift in conversion rate.",
    confidence: 0.95,
    platform: "meta_ads",
    created_at: "2026-03-01T00:00:00Z",
  },
  {
    id: "2",
    category: "efficiency",
    sentiment: "positive",
    priority: 2,
    headline: "CPA decreased by 5.4% to $24.85",
    detail:
      "Cost per acquisition improved across all platforms. Google Ads saw the biggest improvement at -8.2%, while Meta Ads improved by 3.1%.",
    confidence: 0.92,
    created_at: "2026-03-01T00:00:00Z",
  },
  {
    id: "3",
    category: "anomaly",
    sentiment: "attention_needed",
    priority: 3,
    headline: "Unusual spike in Google Ads CPC on Feb 18",
    detail:
      "Cost per click jumped 340% above the rolling average on February 18th ($3.42 vs expected $0.95). This coincided with increased competitor bidding activity.",
    confidence: 0.88,
    platform: "google_ads",
    created_at: "2026-03-01T00:00:00Z",
  },
  {
    id: "4",
    category: "opportunity",
    sentiment: "neutral",
    priority: 4,
    headline: "Meta retargeting audience shows expansion potential",
    detail:
      "The retargeting campaign has a 5.2x ROAS with only 18% of total budget allocated. Increasing budget allocation could yield additional high-quality conversions.",
    confidence: 0.85,
    platform: "meta_ads",
    created_at: "2026-03-01T00:00:00Z",
  },
  {
    id: "5",
    category: "risk",
    sentiment: "attention_needed",
    priority: 5,
    headline: "Display Prospecting campaign burning budget",
    detail:
      "The Display Prospecting campaign has a 0.7x ROAS with $3,100 in spend. It generated only 22 conversions, significantly below the account average of 60 per campaign.",
    confidence: 0.93,
    platform: "google_ads",
    created_at: "2026-03-01T00:00:00Z",
  },
];

const DEMO_RECOMMENDATIONS: Recommendation[] = [
  {
    id: "1",
    category: "budget",
    priority: "high",
    title: "Reallocate $3,100 from Display Prospecting",
    description:
      "Pause the Display Prospecting campaign (0.7x ROAS) and redirect budget to the Summer Sale Retargeting campaign (5.2x ROAS).",
    expected_impact: "Estimated +$12,400 in additional revenue",
    effort: "low",
    action_items: [
      "Pause Display Prospecting campaign",
      "Increase Summer Sale Retargeting daily budget by $100",
      "Monitor performance for 7 days",
    ],
  },
  {
    id: "2",
    category: "creative",
    priority: "medium",
    title: "Refresh Google Ads creative to address CPC spike",
    description:
      "The February 18th CPC spike suggests ad fatigue or increased competition. Refresh ad copy and test new variations.",
    expected_impact: "Reduce CPC by 15-20%",
    effort: "medium",
    action_items: [
      "Create 3 new ad variations",
      "A/B test headlines and descriptions",
      "Review competitor ad library for positioning gaps",
    ],
  },
  {
    id: "3",
    category: "targeting",
    priority: "medium",
    title: "Expand Meta lookalike audiences",
    description:
      "Current retargeting success suggests strong audience signal. Create 1-3% lookalike audiences from recent converters.",
    expected_impact: "Estimated +15% conversion volume at similar CPA",
    effort: "low",
    action_items: [
      "Export last 90 days converter list",
      "Create 1%, 2%, and 3% lookalike audiences",
      "Launch test campaign with $50/day budget",
    ],
  },
];

type FilterCategory = "all" | Insight["category"];

const FILTER_OPTIONS: { label: string; value: FilterCategory }[] = [
  { label: "All", value: "all" },
  { label: "Performance", value: "performance" },
  { label: "Efficiency", value: "efficiency" },
  { label: "Anomaly", value: "anomaly" },
  { label: "Opportunity", value: "opportunity" },
  { label: "Risk", value: "risk" },
];

export function InsightsContent() {
  const [filter, setFilter] = useState<FilterCategory>("all");

  const filteredInsights =
    filter === "all"
      ? DEMO_INSIGHTS
      : DEMO_INSIGHTS.filter((i) => i.category === filter);

  return (
    <>
      <Topbar title="Insights" />
      <div className="space-y-6 p-6">
        <PageHeader
          title="AI-Generated Insights"
          description="Key findings from your latest analysis"
        />

        {/* Filters */}
        <div className="flex flex-wrap gap-2">
          {FILTER_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setFilter(opt.value)}
              className={cn(
                "rounded-full px-4 py-1.5 text-sm font-medium transition-colors",
                filter === opt.value
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200",
              )}
            >
              {opt.label}
              {opt.value !== "all" && (
                <span className="ml-1.5">
                  {DEMO_INSIGHTS.filter((i) => i.category === opt.value).length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Insights */}
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900">
            Insights ({filteredInsights.length})
          </h3>
          {filteredInsights.map((insight) => (
            <InsightCard key={insight.id} insight={insight} />
          ))}
        </div>

        {/* Recommendations */}
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900">
            Recommendations ({DEMO_RECOMMENDATIONS.length})
          </h3>
          {DEMO_RECOMMENDATIONS.map((rec) => (
            <RecommendationCard key={rec.id} recommendation={rec} />
          ))}
        </div>
      </div>
    </>
  );
}
