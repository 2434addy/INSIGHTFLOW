"use client";

import { PageHeader } from "@/components/common/page-header";
import { Topbar } from "@/components/layout/topbar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { KPICard } from "@/components/dashboard/kpi-card";
import { cn, formatCurrency, formatNumber, formatPercent } from "@/lib/utils";
import type { CampaignTier } from "@/types/api";
import {
  ArrowUpDown,
  DollarSign,
  Megaphone,
  ShoppingCart,
  TrendingUp,
} from "lucide-react";
import { useState } from "react";

interface CampaignRow {
  id: string;
  name: string;
  platform: string;
  status: string;
  tier: CampaignTier;
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  ctr: number;
  cpa: number;
  roas: number;
  efficiency_score: number;
}

const DEMO_CAMPAIGNS: CampaignRow[] = [
  { id: "1", name: "Summer Sale - Retargeting", platform: "meta_ads", status: "active", tier: "star", spend: 8200, impressions: 420000, clicks: 12600, conversions: 340, ctr: 3.0, cpa: 24.12, roas: 5.2, efficiency_score: 0.92 },
  { id: "2", name: "Holiday Promo", platform: "meta_ads", status: "active", tier: "star", spend: 4500, impressions: 280000, clicks: 8400, conversions: 210, ctr: 3.0, cpa: 21.43, roas: 4.8, efficiency_score: 0.88 },
  { id: "3", name: "Brand Awareness - Video", platform: "google_ads", status: "active", tier: "strong", spend: 6100, impressions: 350000, clicks: 7000, conversions: 180, ctr: 2.0, cpa: 33.89, roas: 3.9, efficiency_score: 0.74 },
  { id: "4", name: "Shopping - Best Sellers", platform: "google_ads", status: "active", tier: "strong", spend: 3800, impressions: 190000, clicks: 5700, conversions: 145, ctr: 3.0, cpa: 26.21, roas: 3.6, efficiency_score: 0.71 },
  { id: "5", name: "Search - Generic Terms", platform: "google_ads", status: "active", tier: "average", spend: 5200, impressions: 260000, clicks: 5200, conversions: 95, ctr: 2.0, cpa: 54.74, roas: 1.8, efficiency_score: 0.45 },
  { id: "6", name: "Social - Interest Targeting", platform: "meta_ads", status: "active", tier: "average", spend: 2900, impressions: 180000, clicks: 4500, conversions: 68, ctr: 2.5, cpa: 42.65, roas: 2.1, efficiency_score: 0.38 },
  { id: "7", name: "Display - Remarketing", platform: "google_ads", status: "paused", tier: "underperformer", spend: 1800, impressions: 150000, clicks: 1500, conversions: 15, ctr: 1.0, cpa: 120.0, roas: 0.9, efficiency_score: 0.18 },
  { id: "8", name: "Display Prospecting", platform: "google_ads", status: "active", tier: "waster", spend: 3100, impressions: 310000, clicks: 3100, conversions: 22, ctr: 1.0, cpa: 140.91, roas: 0.7, efficiency_score: 0.08 },
];

const TIER_BADGE_VARIANT = {
  star: "success",
  strong: "default",
  average: "neutral",
  underperformer: "warning",
  waster: "danger",
} as const;

const TIER_LABELS: Record<CampaignTier, string> = {
  star: "Star",
  strong: "Strong",
  average: "Average",
  underperformer: "Underperformer",
  waster: "Waster",
};

type SortKey = "spend" | "conversions" | "roas" | "cpa" | "efficiency_score";

export function CampaignsContent() {
  const [sortKey, setSortKey] = useState<SortKey>("efficiency_score");
  const [sortAsc, setSortAsc] = useState(false);
  const [tierFilter, setTierFilter] = useState<CampaignTier | "all">("all");

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  };

  const filtered =
    tierFilter === "all"
      ? DEMO_CAMPAIGNS
      : DEMO_CAMPAIGNS.filter((c) => c.tier === tierFilter);

  const sorted = [...filtered].sort((a, b) => {
    const diff = a[sortKey] - b[sortKey];
    return sortAsc ? diff : -diff;
  });

  const totalSpend = DEMO_CAMPAIGNS.reduce((s, c) => s + c.spend, 0);
  const totalConversions = DEMO_CAMPAIGNS.reduce((s, c) => s + c.conversions, 0);
  const avgRoas =
    DEMO_CAMPAIGNS.reduce((s, c) => s + c.roas * c.spend, 0) / totalSpend;
  const activeCampaigns = DEMO_CAMPAIGNS.filter(
    (c) => c.status === "active",
  ).length;

  return (
    <>
      <Topbar title="Campaigns" />
      <div className="space-y-6 p-6">
        <PageHeader
          title="Campaign Performance"
          description="Performance metrics and tier classification for all campaigns"
        />

        {/* Summary KPIs */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KPICard
            label="Active Campaigns"
            value={String(activeCampaigns)}
            icon={<Megaphone className="h-5 w-5" />}
          />
          <KPICard
            label="Total Spend"
            value={formatCurrency(totalSpend)}
            icon={<DollarSign className="h-5 w-5" />}
          />
          <KPICard
            label="Total Conversions"
            value={formatNumber(totalConversions)}
            icon={<ShoppingCart className="h-5 w-5" />}
          />
          <KPICard
            label="Weighted ROAS"
            value={`${avgRoas.toFixed(2)}x`}
            icon={<TrendingUp className="h-5 w-5" />}
          />
        </div>

        {/* Tier Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Tier Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => setTierFilter("all")}
                className={cn(
                  "rounded-lg border px-4 py-2 text-sm font-medium transition-colors",
                  tierFilter === "all"
                    ? "border-blue-600 bg-blue-50 text-blue-700"
                    : "border-gray-200 text-gray-600 hover:bg-gray-50",
                )}
              >
                All ({DEMO_CAMPAIGNS.length})
              </button>
              {(Object.keys(TIER_LABELS) as CampaignTier[]).map((tier) => {
                const count = DEMO_CAMPAIGNS.filter(
                  (c) => c.tier === tier,
                ).length;
                return (
                  <button
                    key={tier}
                    onClick={() => setTierFilter(tier)}
                    className={cn(
                      "rounded-lg border px-4 py-2 text-sm font-medium transition-colors",
                      tierFilter === tier
                        ? "border-blue-600 bg-blue-50 text-blue-700"
                        : "border-gray-200 text-gray-600 hover:bg-gray-50",
                    )}
                  >
                    {TIER_LABELS[tier]} ({count})
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Campaign Table */}
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-gray-500">
                    <th className="p-4 font-medium">Campaign</th>
                    <th className="p-4 font-medium">Platform</th>
                    <th className="p-4 font-medium">Tier</th>
                    <th className="p-4 font-medium">
                      <SortButton
                        label="Spend"
                        active={sortKey === "spend"}
                        asc={sortAsc}
                        onClick={() => handleSort("spend")}
                      />
                    </th>
                    <th className="p-4 font-medium">
                      <SortButton
                        label="Conv."
                        active={sortKey === "conversions"}
                        asc={sortAsc}
                        onClick={() => handleSort("conversions")}
                      />
                    </th>
                    <th className="p-4 font-medium">CTR</th>
                    <th className="p-4 font-medium">
                      <SortButton
                        label="CPA"
                        active={sortKey === "cpa"}
                        asc={sortAsc}
                        onClick={() => handleSort("cpa")}
                      />
                    </th>
                    <th className="p-4 font-medium">
                      <SortButton
                        label="ROAS"
                        active={sortKey === "roas"}
                        asc={sortAsc}
                        onClick={() => handleSort("roas")}
                      />
                    </th>
                    <th className="p-4 font-medium">
                      <SortButton
                        label="Score"
                        active={sortKey === "efficiency_score"}
                        asc={sortAsc}
                        onClick={() => handleSort("efficiency_score")}
                      />
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {sorted.map((c) => (
                    <tr key={c.id} className="hover:bg-gray-50">
                      <td className="p-4">
                        <div>
                          <p className="font-medium text-gray-900">{c.name}</p>
                          <p className="text-xs text-gray-500">{c.status}</p>
                        </div>
                      </td>
                      <td className="p-4 text-gray-600">
                        {c.platform.replace("_", " ")}
                      </td>
                      <td className="p-4">
                        <Badge variant={TIER_BADGE_VARIANT[c.tier]}>
                          {TIER_LABELS[c.tier]}
                        </Badge>
                      </td>
                      <td className="p-4 text-right text-gray-900">
                        {formatCurrency(c.spend)}
                      </td>
                      <td className="p-4 text-right text-gray-900">
                        {formatNumber(c.conversions)}
                      </td>
                      <td className="p-4 text-right text-gray-900">
                        {formatPercent(c.ctr)}
                      </td>
                      <td className="p-4 text-right text-gray-900">
                        {formatCurrency(c.cpa)}
                      </td>
                      <td className="p-4 text-right text-gray-900">
                        {c.roas.toFixed(2)}x
                      </td>
                      <td className="p-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <div className="h-2 w-16 overflow-hidden rounded-full bg-gray-200">
                            <div
                              className={cn(
                                "h-full rounded-full",
                                c.efficiency_score >= 0.7
                                  ? "bg-green-500"
                                  : c.efficiency_score >= 0.4
                                    ? "bg-amber-500"
                                    : "bg-red-500",
                              )}
                              style={{
                                width: `${c.efficiency_score * 100}%`,
                              }}
                            />
                          </div>
                          <span className="text-gray-600">
                            {(c.efficiency_score * 100).toFixed(0)}
                          </span>
                        </div>
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

function SortButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  asc?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-1 hover:text-gray-900"
    >
      {label}
      <ArrowUpDown
        className={cn("h-3.5 w-3.5", active ? "text-blue-600" : "text-gray-400")}
      />
    </button>
  );
}
