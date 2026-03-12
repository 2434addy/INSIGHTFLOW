import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { TrendingDown, TrendingUp, Minus } from "lucide-react";
import type { ReactNode } from "react";

interface KPICardProps {
  label: string;
  value: string;
  change?: number | null;
  changeLabel?: string;
  icon?: ReactNode;
}

export function KPICard({ label, value, change, changeLabel, icon }: KPICardProps) {
  const isPositive = change != null && change > 0;
  const isNegative = change != null && change < 0;
  const isNeutral = change == null || change === 0;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-gray-500">{label}</p>
          {icon && <div className="text-gray-400">{icon}</div>}
        </div>
        <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
        {change != null && (
          <div className="mt-2 flex items-center gap-1">
            {isPositive && <TrendingUp className="h-4 w-4 text-green-600" />}
            {isNegative && <TrendingDown className="h-4 w-4 text-red-600" />}
            {isNeutral && <Minus className="h-4 w-4 text-gray-400" />}
            <span
              className={cn(
                "text-sm font-medium",
                isPositive && "text-green-600",
                isNegative && "text-red-600",
                isNeutral && "text-gray-500",
              )}
            >
              {isPositive ? "+" : ""}
              {change.toFixed(1)}%
            </span>
            {changeLabel && (
              <span className="text-sm text-gray-500">{changeLabel}</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
