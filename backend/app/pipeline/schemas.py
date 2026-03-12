"""
Pydantic schemas for data flowing between pipeline stages.

These typed models define the contract between agents, ensuring
each stage produces exactly what downstream stages expect.
"""

import uuid
from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────


class MetricDirection(str, Enum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    NEUTRAL = "neutral"


class TrendDirection(str, Enum):
    ACCELERATING = "accelerating"
    INCREASING = "increasing"
    STABLE = "stable"
    DECREASING = "decreasing"
    DECLINING = "declining"
    INSUFFICIENT_DATA = "insufficient_data"


class AnomalyType(str, Enum):
    SPIKE = "spike"
    DROP = "drop"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CampaignTier(str, Enum):
    STAR = "star"
    STRONG = "strong"
    AVERAGE = "average"
    UNDERPERFORMER = "underperformer"
    WASTER = "waster"


class InsightCategory(str, Enum):
    PERFORMANCE = "performance"
    EFFICIENCY = "efficiency"
    GROWTH = "growth"
    ANOMALY = "anomaly"
    OPPORTUNITY = "opportunity"
    RISK = "risk"


class InsightSentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    ATTENTION_NEEDED = "attention_needed"


class RecommendationCategory(str, Enum):
    BUDGET = "budget"
    TARGETING = "targeting"
    CREATIVE = "creative"
    BIDDING = "bidding"
    SCHEDULING = "scheduling"


class PipelineStage(str, Enum):
    DATA_VALIDATION = "data_validation"
    KPI_COMPUTATION = "kpi_computation"
    TREND_DETECTION = "trend_detection"
    ANOMALY_DETECTION = "anomaly_detection"
    CAMPAIGN_EVALUATION = "campaign_evaluation"
    INSIGHT_GENERATION = "insight_generation"
    RECOMMENDATION_GENERATION = "recommendation_generation"
    REPORT_ASSEMBLY = "report_assembly"


# ── Core Metric Record ──────────────────────────────────────────


class MetricRecord(BaseModel):
    """A single day's metrics for one campaign."""

    campaign_id: uuid.UUID
    campaign_name: str = ""
    platform: str
    date: date
    organization_id: uuid.UUID

    # Core metrics
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    conversions: int = 0
    conversion_value: float = 0.0

    # Derived metrics (computed by KPI skill)
    ctr: Optional[float] = None
    cpc: Optional[float] = None
    cpa: Optional[float] = None
    roas: Optional[float] = None
    cvr: Optional[float] = None
    cpm: Optional[float] = None
    aov: Optional[float] = None


class DatedValue(BaseModel):
    """A metric value with its date — used for time-series analysis."""

    date: date
    value: float


# ── Validation ──────────────────────────────────────────────────


class ValidationIssue(BaseModel):
    level: str = "error"  # error | warning | info
    message: str
    record_index: Optional[int] = None
    field: Optional[str] = None
    auto_fixable: bool = False


class ValidationResult(BaseModel):
    total_records: int
    valid_records: int
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def error_rate(self) -> float:
        return len(self.errors) / self.total_records if self.total_records > 0 else 0.0


# ── KPI / Summary ──────────────────────────────────────────────


class SummaryMetrics(BaseModel):
    """Aggregated metrics across all campaigns in a period."""

    spend: float = 0.0
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    conversion_value: float = 0.0
    ctr: Optional[float] = None
    cpc: Optional[float] = None
    cpa: Optional[float] = None
    roas: Optional[float] = None
    cvr: Optional[float] = None
    cpm: Optional[float] = None
    aov: Optional[float] = None


class PeriodComparison(BaseModel):
    """Absolute and percentage changes between two periods."""

    spend_delta: float = 0.0
    spend_change_pct: Optional[float] = None
    impressions_delta: int = 0
    impressions_change_pct: Optional[float] = None
    clicks_delta: int = 0
    clicks_change_pct: Optional[float] = None
    conversions_delta: int = 0
    conversions_change_pct: Optional[float] = None
    conversion_value_delta: float = 0.0
    conversion_value_change_pct: Optional[float] = None
    roas_delta: Optional[float] = None
    roas_change_pct: Optional[float] = None
    cpa_delta: Optional[float] = None
    cpa_change_pct: Optional[float] = None
    ctr_delta: Optional[float] = None
    ctr_change_pct: Optional[float] = None


class KPIResult(BaseModel):
    """Output of the KPI computation stage."""

    current_period: SummaryMetrics
    previous_period: Optional[SummaryMetrics] = None
    comparison: Optional[PeriodComparison] = None
    by_platform: dict[str, SummaryMetrics] = Field(default_factory=dict)
    by_campaign: dict[str, SummaryMetrics] = Field(default_factory=dict)
    daily_totals: list[SummaryMetrics] = Field(default_factory=list)
    records: list[MetricRecord] = Field(default_factory=list)


# ── Trend Detection ─────────────────────────────────────────────


class TrendResult(BaseModel):
    metric: str
    direction: TrendDirection
    strength: float = 0.0
    slope: float = 0.0
    normalized_slope_pct: float = 0.0
    r_squared: float = 0.0


class MovingAverages(BaseModel):
    metric: str
    windows: dict[int, float] = Field(default_factory=dict)


class PacingResult(BaseModel):
    status: str  # on_track | underspending | overspending
    pacing_ratio: float = 0.0
    total_spent: float = 0.0
    expected_spent: float = 0.0
    projected_total: float = 0.0
    budget: float = 0.0
    days_remaining: int = 0


class TrendAnalysis(BaseModel):
    """Output of the trend detection stage."""

    trends: list[TrendResult] = Field(default_factory=list)
    moving_averages: list[MovingAverages] = Field(default_factory=list)
    pacing: Optional[PacingResult] = None


# ── Anomaly Detection ───────────────────────────────────────────


class AnomalyPoint(BaseModel):
    metric: str = ""
    index: int = 0
    anomaly_date: Optional[date] = None
    value: float = 0.0
    expected: Optional[float] = None
    z_score: Optional[float] = None
    type: AnomalyType = AnomalyType.SPIKE
    severity: Severity = Severity.LOW
    deviation_pct: Optional[float] = None
    context: Optional[str] = None


class CorrelationAnomaly(BaseModel):
    metric_pair: tuple[str, str]
    historical_correlation: float
    recent_correlation: float
    significance: str = "medium"


class AnomalyAnalysis(BaseModel):
    """Output of the anomaly detection stage."""

    point_anomalies: list[AnomalyPoint] = Field(default_factory=list)
    correlation_anomalies: list[CorrelationAnomaly] = Field(default_factory=list)
    missing_dates: list[date] = Field(default_factory=list)


# ── Campaign Evaluation ─────────────────────────────────────────


class TieredCampaign(BaseModel):
    campaign_id: uuid.UUID
    campaign_name: str
    platform: str
    tier: CampaignTier
    efficiency_score: float
    percentile: float
    spend: float = 0.0
    roas: Optional[float] = None
    cpa: Optional[float] = None
    conversions: int = 0


class BudgetAssessment(BaseModel):
    tier_distribution: dict[str, dict] = Field(default_factory=dict)
    reallocation_potential: float = 0.0
    is_well_allocated: bool = True
    estimated_impact: str = ""


class CampaignEvaluationResult(BaseModel):
    """Output of the campaign evaluation stage."""

    tiered_campaigns: dict[str, list[TieredCampaign]] = Field(default_factory=dict)
    budget_assessment: BudgetAssessment = Field(default_factory=BudgetAssessment)
    top_performers: list[TieredCampaign] = Field(default_factory=list)
    bottom_performers: list[TieredCampaign] = Field(default_factory=list)
    platform_comparison: dict = Field(default_factory=dict)


# ── Insight Generation ──────────────────────────────────────────


class GeneratedInsight(BaseModel):
    category: InsightCategory
    sentiment: InsightSentiment
    priority: int = 1
    headline: str
    detail: str
    supporting_data: dict = Field(default_factory=dict)
    confidence: float = 0.95
    campaign_id: Optional[uuid.UUID] = None
    platform: Optional[str] = None


class InsightGenerationResult(BaseModel):
    """Output of the insight generation stage."""

    insights: list[GeneratedInsight] = Field(default_factory=list)
    executive_summary: str = ""
    ai_model: str = ""
    tokens_used: int = 0


# ── Recommendation Generation ───────────────────────────────────


class GeneratedRecommendation(BaseModel):
    category: RecommendationCategory
    priority: str = "medium"  # critical | high | medium | low
    title: str
    description: str
    expected_impact: str = ""
    estimated_impact_value: Optional[float] = None
    effort: str = "medium"  # low | medium | high
    action_items: list[str] = Field(default_factory=list)
    campaign_id: Optional[uuid.UUID] = None
    platform: Optional[str] = None


class RecommendationResult(BaseModel):
    """Output of the recommendation generation stage."""

    recommendations: list[GeneratedRecommendation] = Field(default_factory=list)
    ai_model: str = ""
    tokens_used: int = 0


# ── Report Request / Result ─────────────────────────────────────


class ReportRequest(BaseModel):
    """Input to the report generation pipeline."""

    report_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    organization_id: uuid.UUID
    generated_by: uuid.UUID
    date_range_start: date
    date_range_end: date
    comparison_period: str = "previous_period"  # previous_period | previous_year
    platforms: list[str] = Field(default_factory=list)
    tone: str = "executive"  # executive | detailed | casual
    ai_model: str = "claude-sonnet-4-6"
    title: str = ""
    template: str = "monthly_performance"


class PipelineProgress(BaseModel):
    report_id: uuid.UUID
    stage: PipelineStage
    pct: int = 0
    message: str = ""


class PipelineResult(BaseModel):
    """Final output of the complete analytics pipeline."""

    report_id: uuid.UUID
    validation: ValidationResult
    kpis: KPIResult
    trends: TrendAnalysis
    anomalies: AnomalyAnalysis
    campaign_evaluation: CampaignEvaluationResult
    insights: InsightGenerationResult
    recommendations: RecommendationResult
    total_tokens_used: int = 0
    total_ai_cost: float = 0.0
