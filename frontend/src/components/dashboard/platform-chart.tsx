"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/utils";
import type { KPISummary } from "@/types/api";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

interface PlatformChartProps {
  data: Record<string, KPISummary>;
}

const PLATFORM_COLORS: Record<string, string> = {
  meta_ads: "#1877F2",
  google_ads: "#4285F4",
  ga4: "#E37400",
  shopify: "#96BF48",
};

const PLATFORM_LABELS: Record<string, string> = {
  meta_ads: "Meta Ads",
  google_ads: "Google Ads",
  ga4: "Google Analytics",
  shopify: "Shopify",
};

export function PlatformChart({ data }: PlatformChartProps) {
  const chartData = Object.entries(data).map(([platform, summary]) => ({
    name: PLATFORM_LABELS[platform] || platform,
    value: summary.spend,
    color: PLATFORM_COLORS[platform] || "#6b7280",
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Spend by Platform</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={110}
                dataKey="value"
                nameKey="name"
                paddingAngle={2}
              >
                {chartData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number) => formatCurrency(value)}
                contentStyle={{
                  borderRadius: "8px",
                  border: "1px solid #e5e7eb",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        {/* Legend */}
        <div className="mt-4 flex flex-wrap justify-center gap-4">
          {chartData.map((entry) => (
            <div key={entry.name} className="flex items-center gap-2">
              <div
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm text-gray-600">{entry.name}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
