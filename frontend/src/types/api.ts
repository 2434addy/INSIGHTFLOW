export type Platform = "meta_ads" | "google_ads" | "ga4" | "shopify";

export type ReportStatus = "generating" | "completed" | "failed";

export type InsightCategory =
  | "performance"
  | "efficiency"
  | "growth"
  | "anomaly"
  | "opportunity"
  | "risk";

export type InsightSentiment = "positive" | "neutral" | "attention_needed";

export type CampaignTier =
  | "star"
  | "strong"
  | "average"
  | "underperformer"
  | "waster";

export type TrendDirection =
  | "accelerating"
  | "increasing"
  | "stable"
  | "decreasing"
  | "declining";

export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
}

export interface KPISummary {
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  conversion_value: number;
  ctr: number | null;
  cpc: number | null;
  cpa: number | null;
  roas: number | null;
}

export interface PeriodComparison {
  spend_change_pct: number | null;
  conversions_change_pct: number | null;
  roas_change_pct: number | null;
  cpa_change_pct: number | null;
  ctr_change_pct: number | null;
}

export interface DashboardOverview {
  current_period: KPISummary;
  previous_period: KPISummary | null;
  comparison: PeriodComparison | null;
  by_platform: Record<string, KPISummary>;
  daily_metrics: DailyMetric[];
}

export interface DailyMetric {
  date: string;
  spend: number;
  conversions: number;
  impressions: number;
  clicks: number;
}

export interface CampaignPerformance {
  campaign_id: string;
  campaign_name: string;
  platform: Platform;
  tier: CampaignTier;
  efficiency_score: number;
  spend: number;
  conversions: number;
  roas: number | null;
  cpa: number | null;
  ctr: number | null;
  trend: TrendDirection;
}

export interface Insight {
  id: string;
  category: InsightCategory;
  sentiment: InsightSentiment;
  priority: number;
  headline: string;
  detail: string;
  confidence: number;
  campaign_id?: string;
  platform?: Platform;
  created_at: string;
}

export interface Recommendation {
  id: string;
  category: string;
  priority: string;
  title: string;
  description: string;
  expected_impact: string;
  effort: string;
  action_items: string[];
}

export interface Report {
  id: string;
  title: string;
  status: ReportStatus;
  date_range_start: string;
  date_range_end: string;
  platforms: Platform[];
  tone: string;
  created_at: string;
  pdf_url?: string;
  executive_summary?: string;
  insights: Insight[];
  recommendations: Recommendation[];
  summary_data: DashboardOverview;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
