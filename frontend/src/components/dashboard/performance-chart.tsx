"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DailyMetric } from "@/types/api";
import { formatCompact, formatCurrency } from "@/lib/utils";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface PerformanceChartProps {
  data: DailyMetric[];
  title?: string;
}

export function PerformanceChart({
  data,
  title = "Spend & Conversions",
}: PerformanceChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12, fill: "#6b7280" }}
                tickFormatter={(val: string) =>
                  new Date(val).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                  })
                }
              />
              <YAxis
                yAxisId="spend"
                orientation="left"
                tick={{ fontSize: 12, fill: "#6b7280" }}
                tickFormatter={(val: number) => formatCurrency(val, 0)}
              />
              <YAxis
                yAxisId="conversions"
                orientation="right"
                tick={{ fontSize: 12, fill: "#6b7280" }}
                tickFormatter={(val: number) => formatCompact(val)}
              />
              <Tooltip
                contentStyle={{
                  borderRadius: "8px",
                  border: "1px solid #e5e7eb",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
                }}
                formatter={(value: number, name: string) => [
                  name === "spend"
                    ? formatCurrency(value)
                    : formatCompact(value),
                  name === "spend" ? "Spend" : "Conversions",
                ]}
                labelFormatter={(label: string) =>
                  new Date(label).toLocaleDateString("en-US", {
                    weekday: "short",
                    month: "short",
                    day: "numeric",
                  })
                }
              />
              <Line
                yAxisId="spend"
                type="monotone"
                dataKey="spend"
                stroke="#2563eb"
                strokeWidth={2}
                dot={false}
                name="spend"
              />
              <Line
                yAxisId="conversions"
                type="monotone"
                dataKey="conversions"
                stroke="#16a34a"
                strokeWidth={2}
                dot={false}
                name="conversions"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
