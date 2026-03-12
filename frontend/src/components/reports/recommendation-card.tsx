import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { Recommendation } from "@/types/api";

const PRIORITY_VARIANT = {
  critical: "danger",
  high: "warning",
  medium: "default",
  low: "neutral",
} as const;

interface RecommendationCardProps {
  recommendation: Recommendation;
}

export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const variant =
    PRIORITY_VARIANT[recommendation.priority as keyof typeof PRIORITY_VARIANT] ||
    "neutral";

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-semibold text-gray-900">
                {recommendation.title}
              </h4>
              <Badge variant={variant}>{recommendation.priority}</Badge>
              <Badge variant="outline">{recommendation.effort} effort</Badge>
            </div>
            <p className="mt-1 text-sm text-gray-600">
              {recommendation.description}
            </p>
            {recommendation.expected_impact && (
              <p className="mt-2 text-sm font-medium text-blue-600">
                Expected: {recommendation.expected_impact}
              </p>
            )}
          </div>
        </div>
        {recommendation.action_items.length > 0 && (
          <ul className="mt-3 space-y-1">
            {recommendation.action_items.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-gray-400" />
                {item}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
