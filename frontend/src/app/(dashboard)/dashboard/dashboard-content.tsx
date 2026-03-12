"use client";

import { KPICard } from "@/components/dashboard/kpi-card";
import { PerformanceChart } from "@/components/dashboard/performance-chart";
import { PlatformChart } from "@/components/dashboard/platform-chart";
import { PageHeader } from "@/components/common/page-header";
import { Topbar } from "@/components/layout/topbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatCurrency, formatNumber } from "@/lib/utils";
import type { DailyMetric, KPISummary } from "@/types/api";
import {
  DollarSign,
  MousePointerClick,
  ShoppingCart,
  TrendingUp,
  FileText,
} from "lucide-react";
import Link from "next/link";

// Demo data for initial rendering — replaced by API calls in production
const DEMO_SUMMARY: KPISummary = {
  spend: 45230.5,
  impressions: 2_340_000,
  clicks: 52_400,
  conversions: 1_820,
  conversion_value: 182_400,
  ctr: 2.24,
  cpc: 0.86,
  cpa: 24.85,
  roas: 4.03,
};

const DEMO_COMPARISON = {
  spend_change_pct: 8.2,
  conversions_change_pct: 12.5,
  roas_change_pct: 3.1,
  cpa_change_pct: -5.4,
  ctr_change_pct: 1.8,
};

const DEMO_DAILY: DailyMetric[] = Array.from({ length: 30 }, (_, i) => {
  const d = new Date(2026, 1, i + 1);
  return {
    date: d.toISOString().split("T")[0],
    spend: 1200 + Math.random() * 600 + i * 10,
    conversions: 40 + Math.floor(Math.random() * 30) + Math.floor(i * 0.8),
    impressions: 60000 + Math.floor(Math.random() * 20000),
    clicks: 1500 + Math.floor(Math.random() * 500),
  };
});

const DEMO_PLATFORMS: Record<string, KPISummary> = {
  meta_ads: { ...DEMO_SUMMARY, spend: 22000, conversions: 950, roas: 4.2, ctr: 2.5, cpc: 0.78, cpa: 23.16, impressions: 1_200_000, clicks: 28000, conversion_value: 92400 },
  google_ads: { ...DEMO_SUMMARY, spend: 18500, conversions: 720, roas: 3.8, ctr: 1.9, cpc: 0.95, cpa: 25.69, impressions: 980_000, clicks: 19500, conversion_value: 70300 },
  shopify: { ...DEMO_SUMMARY, spend: 4730, conversions: 150, roas: 4.1, ctr: 3.1, cpc: 0.62, cpa: 31.53, impressions: 160_000, clicks: 4900, conversion_value: 19700 },
};

const DEMO_CAMPAIGNS = [
  { name: "Summer Sale - Retargeting", platform: "meta_ads", spend: 8200, conversions: 340, roas: 5.2, tier: "star" as const },
  { name: "Brand Awareness - Video", platform: "google_ads", spend: 6100, conversions: 180, roas: 3.9, tier: "strong" as const },
  { name: "Holiday Promo", platform: "meta_ads", spend: 4500, conversions: 210, roas: 4.8, tier: "star" as const },
  { name: "Search - Generic Terms", platform: "google_ads", spend: 5200, conversions: 95, roas: 1.8, tier: "average" as const },
  { name: "Display Prospecting", platform: "google_ads", spend: 3100, conversions: 22, roas: 0.7, tier: "waster" as const },
];

const TIER_BADGE_VARIANT = {
  star: "success",
  strong: "default",
  average: "neutral",
  underperformer: "warning",
  waster: "danger",
} as const;

export function DashboardContent() {
  return (
    <>
      <Topbar title="Dashboard" />
      <div className="space-y-6 p-6">
        <PageHeader
          title="Performance Overview"
          description="Last 30 days vs. previous period"
          actions={
            <Link href="/reports">
              <Button>
                <FileText className="h-4 w-4" />
                Generate Report
              </Button>
            </Link>
          }
        />

        {/* KPI Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KPICard
            label="Total Spend"
            value={formatCurrency(DEMO_SUMMARY.spend)}
            change={DEMO_COMPARISON.spend_change_pct}
            changeLabel="vs prev period"
            icon={<DollarSign className="h-5 w-5" />}
          />
          <KPICard
            label="Conversions"
            value={formatNumber(DEMO_SUMMARY.conversions)}
            change={DEMO_COMPARISON.conversions_change_pct}
            changeLabel="vs prev period"
            icon={<ShoppingCart className="h-5 w-5" />}
          />
          <KPICard
            label="ROAS"
            value={`${DEMO_SUMMARY.roas?.toFixed(2)}x`}
            change={DEMO_COMPARISON.roas_change_pct}
            changeLabel="vs prev period"
            icon={<TrendingUp className="h-5 w-5" />}
          />
          <KPICard
            label="CPA"
            value={formatCurrency(DEMO_SUMMARY.cpa ?? 0)}
            change={DEMO_COMPARISON.cpa_change_pct}
            changeLabel="vs prev period"
            icon={<MousePointerClick className="h-5 w-5" />}
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <PerformanceChart data={DEMO_DAILY} />
          </div>
          <PlatformChart data={DEMO_PLATFORMS} />
        </div>

        {/* Campaign Performance Table */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Top Campaigns</CardTitle>
              <Link href="/campaigns">
                <Button variant="ghost" size="sm">
                  View all
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-gray-500">
                    <th className="pb-3 font-medium">Campaign</th>
                    <th className="pb-3 font-medium">Platform</th>
                    <th className="pb-3 font-medium text-right">Spend</th>
                    <th className="pb-3 font-medium text-right">Conv.</th>
                    <th className="pb-3 font-medium text-right">ROAS</th>
                    <th className="pb-3 font-medium">Tier</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {DEMO_CAMPAIGNS.map((c) => (
                    <tr key={c.name} className="hover:bg-gray-50">
                      <td className="py-3 font-medium text-gray-900">
                        {c.name}
                      </td>
                      <td className="py-3 text-gray-600">{c.platform.replace("_", " ")}</td>
                      <td className="py-3 text-right text-gray-900">
                        {formatCurrency(c.spend)}
                      </td>
                      <td className="py-3 text-right text-gray-900">
                        {formatNumber(c.conversions)}
                      </td>
                      <td className="py-3 text-right text-gray-900">
                        {c.roas.toFixed(2)}x
                      </td>
                      <td className="py-3">
                        <Badge variant={TIER_BADGE_VARIANT[c.tier]}>
                          {c.tier}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
