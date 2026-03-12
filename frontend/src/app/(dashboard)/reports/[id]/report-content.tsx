"use client";

import { InsightCard } from "@/components/reports/insight-card";
import { RecommendationCard } from "@/components/reports/recommendation-card";
import { KPICard } from "@/components/dashboard/kpi-card";
import { PerformanceChart } from "@/components/dashboard/performance-chart";
import { PageHeader } from "@/components/common/page-header";
import { Topbar } from "@/components/layout/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency, formatNumber } from "@/lib/utils";
import type { DailyMetric, Insight, Recommendation } from "@/types/api";
import {
  ArrowLeft,
  DollarSign,
  Download,
  MousePointerClick,
  Share2,
  ShoppingCart,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";

interface ReportContentProps {
  reportId: string;
}

const DEMO_DAILY: DailyMetric[] = Array.from({ length: 28 }, (_, i) => {
  const d = new Date(2026, 1, i + 1);
  return {
    date: d.toISOString().split("T")[0],
    spend: 1400 + Math.random() * 400 + i * 8,
    conversions: 50 + Math.floor(Math.random() * 25) + Math.floor(i * 0.6),
    impressions: 70000 + Math.floor(Math.random() * 15000),
    clicks: 1600 + Math.floor(Math.random() * 400),
  };
});

const DEMO_INSIGHTS: Insight[] = [
  {
    id: "1",
    category: "performance",
    sentiment: "positive",
    priority: 1,
    headline: "Conversions up 12.5% month-over-month",
    detail:
      "Total conversions grew from 1,618 to 1,820, driven by Meta retargeting campaigns with a 23% lift in conversion rate.",
    confidence: 0.95,
    created_at: "2026-03-01T00:00:00Z",
  },
  {
    id: "2",
    category: "risk",
    sentiment: "attention_needed",
    priority: 2,
    headline: "Display Prospecting campaign has 0.7x ROAS",
    detail:
      "$3,100 spent with only 22 conversions. Recommend pausing and reallocating budget to top performers.",
    confidence: 0.93,
    created_at: "2026-03-01T00:00:00Z",
  },
  {
    id: "3",
    category: "opportunity",
    sentiment: "neutral",
    priority: 3,
    headline: "Retargeting budget can be expanded profitably",
    detail:
      "Summer Sale Retargeting has 5.2x ROAS with only 18% of budget. Increasing allocation could yield more high-value conversions.",
    confidence: 0.85,
    created_at: "2026-03-01T00:00:00Z",
  },
];

const DEMO_RECOMMENDATIONS: Recommendation[] = [
  {
    id: "1",
    category: "budget",
    priority: "high",
    title: "Reallocate $3,100 from Display Prospecting to retargeting",
    description:
      "Pause Display Prospecting (0.7x ROAS) and redirect to Summer Sale Retargeting (5.2x ROAS).",
    expected_impact: "Estimated +$12,400 additional revenue",
    effort: "low",
    action_items: [
      "Pause Display Prospecting campaign",
      "Increase retargeting daily budget by $100",
    ],
  },
  {
    id: "2",
    category: "creative",
    priority: "medium",
    title: "Refresh Google Ads creative",
    description:
      "Address CPC spike by testing new ad variations and reviewing competitor positioning.",
    expected_impact: "Reduce CPC by 15-20%",
    effort: "medium",
    action_items: [
      "Create 3 new ad variations",
      "A/B test headlines",
    ],
  },
];

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function ReportContent({ reportId }: ReportContentProps) {
  return (
    <>
      <Topbar title="Report Viewer" />
      <div className="space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/dashboard">
            <Button variant="ghost" size="icon" aria-label="Back to dashboard">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div className="flex-1">
            <PageHeader
              title="February 2026 Performance Report"
              description="Feb 1 - Feb 28, 2026 vs. previous period"
              actions={
                <div className="flex gap-2">
                  <Button variant="outline">
                    <Share2 className="h-4 w-4" />
                    Share
                  </Button>
                  <Button>
                    <Download className="h-4 w-4" />
                    Export PDF
                  </Button>
                </div>
              }
            />
          </div>
        </div>

        {/* Report metadata */}
        <div className="flex items-center gap-3">
          <Badge variant="success">Completed</Badge>
          <Badge variant="outline">Executive Tone</Badge>
          <Badge variant="outline">Meta Ads</Badge>
          <Badge variant="outline">Google Ads</Badge>
          <span className="text-sm text-gray-500">
            Generated Mar 1, 2026 at 10:32 AM
          </span>
        </div>

        {/* Executive Summary */}
        <Card>
          <CardHeader>
            <CardTitle>Executive Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none text-gray-700">
              <p>
                February delivered strong performance improvements across all
                key metrics. Total conversions rose 12.5% to 1,820 while ROAS
                improved to 4.03x from 3.91x in the prior period, reflecting
                better budget allocation toward high-performing retargeting
                campaigns.
              </p>
              <p>
                Meta Ads continues to outperform with a 4.2x ROAS, though Google
                Ads showed the biggest CPA improvement at -8.2%. The Display
                Prospecting campaign remains the primary efficiency drag with
                $3,100 spent at just 0.7x ROAS, representing the most
                significant budget reallocation opportunity.
              </p>
              <p>
                Looking ahead, expanding retargeting audience reach and
                refreshing Google Ads creative should sustain the positive
                momentum into March.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* KPI Summary */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KPICard
            label="Total Spend"
            value={formatCurrency(45230)}
            change={8.2}
            icon={<DollarSign className="h-5 w-5" />}
          />
          <KPICard
            label="Conversions"
            value={formatNumber(1820)}
            change={12.5}
            icon={<ShoppingCart className="h-5 w-5" />}
          />
          <KPICard
            label="ROAS"
            value="4.03x"
            change={3.1}
            icon={<TrendingUp className="h-5 w-5" />}
          />
          <KPICard
            label="CPA"
            value={formatCurrency(24.85)}
            change={-5.4}
            icon={<MousePointerClick className="h-5 w-5" />}
          />
        </div>

        {/* Performance Chart */}
        <PerformanceChart data={DEMO_DAILY} title="Daily Performance Trend" />

        {/* Insights Section */}
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900">Key Insights</h3>
          {DEMO_INSIGHTS.map((insight) => (
            <InsightCard key={insight.id} insight={insight} />
          ))}
        </div>

        {/* Recommendations Section */}
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900">
            Recommendations
          </h3>
          {DEMO_RECOMMENDATIONS.map((rec) => (
            <RecommendationCard key={rec.id} recommendation={rec} />
          ))}
        </div>
      </div>
    </>
  );
}
