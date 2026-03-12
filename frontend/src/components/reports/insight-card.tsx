import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { Insight } from "@/types/api";
import {
  AlertTriangle,
  ArrowUpRight,
  Lightbulb,
  TrendingUp,
  Zap,
  Shield,
} from "lucide-react";

const CATEGORY_ICONS: Record<string, typeof Lightbulb> = {
  performance: TrendingUp,
  efficiency: Zap,
  growth: ArrowUpRight,
  anomaly: AlertTriangle,
  opportunity: Lightbulb,
  risk: Shield,
};

const SENTIMENT_VARIANT = {
  positive: "success",
  neutral: "neutral",
  attention_needed: "warning",
} as const;

interface InsightCardProps {
  insight: Insight;
}

export function InsightCard({ insight }: InsightCardProps) {
  const Icon = CATEGORY_ICONS[insight.category] || Lightbulb;
  const sentimentVariant = SENTIMENT_VARIANT[insight.sentiment] || "neutral";

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div
            className={cn(
              "mt-0.5 rounded-lg p-2",
              insight.sentiment === "positive" && "bg-green-100 text-green-700",
              insight.sentiment === "attention_needed" &&
                "bg-amber-100 text-amber-700",
              insight.sentiment === "neutral" && "bg-gray-100 text-gray-700",
            )}
          >
            <Icon className="h-4 w-4" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-semibold text-gray-900">
                {insight.headline}
              </h4>
              <Badge variant={sentimentVariant}>{insight.category}</Badge>
            </div>
            <p className="mt-1 text-sm text-gray-600">{insight.detail}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
