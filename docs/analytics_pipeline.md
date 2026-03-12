# InsightFlow — Analytics Pipeline Implementation

## Overview

The analytics pipeline transforms raw marketing metric data into AI-generated insights and client-ready reports. It is implemented as a DAG-based orchestrator coordinating 8 agents, each backed by reusable skill modules.

**Target execution time:** < 45 seconds per report
**Fallback guarantee:** Pipeline always completes — AI failures degrade to template-based output, never to errors

---

## Architecture

```
                          ReportRequest + MetricRecord[]
                                     │
                    ┌────────────────▼────────────────┐
                    │       PipelineOrchestrator       │
                    │   (DAG execution coordinator)    │
                    └────────────────┬────────────────┘
                                     │
              ┌──────────────────────▼──────────────────────┐
              │                                             │
    ┌─────────▼─────────┐                                   │
    │  Stage 1: Validate │ ─── RawDataValidator             │
    └─────────┬─────────┘                                   │
              │                                             │
    ┌─────────▼─────────┐                                   │
    │  Stage 2: KPIs     │ ─── KPIComputer, Aggregator,     │  Sequential
    │                    │     PeriodComparer, Efficiency    │
    └─────────┬─────────┘                                   │
              │                                             │
         ┌────┴────┐                                        │
         │         │                                        │
    ┌────▼────┐ ┌──▼──────────┐                             │
    │ Stage 3 │ │  Stage 4    │  ← asyncio.gather()         │
    │ Trends  │ │  Anomalies  │    (parallel execution)     │
    └────┬────┘ └──┬──────────┘                             │
         │         │                                        │
         └────┬────┘                                        │
              │                                             │
    ┌─────────▼─────────┐                                   │
    │  Stage 5: Campaign │ ─── TierClassifier,              │
    │  Evaluation        │     BudgetAssessor               │
    └─────────┬─────────┘                                   │
              │                                             │
    ┌─────────▼─────────┐                                   │
    │  Stage 6: Insights │ ─── Claude API + fallback        │
    │                    │     InsightPromptBuilder          │
    └─────────┬─────────┘                                   │
              │                                             │
    ┌─────────▼─────────┐                                   │
    │  Stage 7: Recs     │ ─── Claude API + fallback        │
    └─────────┬─────────┘                                   │
              │                                             │
    ┌─────────▼─────────┐                                   │
    │  Stage 8: Assembly │ ─── Cost estimate, final result  │
    └─────────┬─────────┘                                   │
              │                                             │
              └──────────────────────▼──────────────────────┘
                                     │
                              PipelineResult
```

---

## Entry Points

### 1. Celery Task (Production)

```python
# app/tasks/report_tasks.py
@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def generate_report(self, report_id: str) -> None:
    """
    1. Load Report from DB (status='generating')
    2. Fetch MetricRecord[] from metrics table for date range + workspace
    3. Build ReportRequest from Report config
    4. Run PipelineOrchestrator.execute() with progress_callback → Redis
    5. Persist insights + recommendations to DB
    6. Update Report status → 'completed'
    7. Generate PDF → upload to S3 → store pdf_url
    8. On failure → status='failed', error_message stored
    """
```

**Triggered by:** `POST /v1/reports/generate` → `ReportService.generate()` → `generate_report.delay(report_id)`

**Progress tracking:** Callback writes to Redis key `report_progress:{report_id}`:

```json
{ "percent": 55, "current_stage": "insight_generation", "stages": {...} }
```

**Polled by:** `GET /v1/reports/:id/status` reads from Redis.

### 2. Direct Invocation (Testing / CLI)

```python
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.schemas import ReportRequest, MetricRecord

orchestrator = PipelineOrchestrator(anthropic_client=None)  # None = template fallback
result = await orchestrator.execute(request, records, progress_callback=on_progress)
```

---

## Pipeline Orchestrator

**File:** `app/pipeline/orchestrator.py`

The orchestrator initializes all 8 agents in its constructor and executes them in a fixed DAG order. Stages 3 and 4 run in parallel via `asyncio.gather()`.

```python
class PipelineOrchestrator:
    def __init__(self, anthropic_client=None):
        self._data_validation = DataValidationAgent()
        self._kpi_computation = KPIComputationAgent()
        self._trend_detection = TrendDetectionAgent()
        self._anomaly_detection = AnomalyDetectionAgent()
        self._campaign_evaluation = CampaignEvaluationAgent()
        self._insight_generation = InsightGenerationAgent(anthropic_client)
        self._recommendation = RecommendationAgent(anthropic_client)
        self._report_generation = ReportGenerationAgent()

    async def execute(
        self,
        request: ReportRequest,
        records: list[MetricRecord],
        progress_callback: Callable[[PipelineProgress], None] | None = None,
    ) -> PipelineResult:
```

### Execution Sequence

| Order | Stage | Agent | Progress % | Parallel |
|:-----:|-------|-------|:----------:|:--------:|
| 1 | Data Validation | `DataValidationAgent` | 5% | — |
| 2 | KPI Computation | `KPIComputationAgent` | 15% | — |
| 3 | Trend Detection | `TrendDetectionAgent` | 25% | Yes (with 4) |
| 4 | Anomaly Detection | `AnomalyDetectionAgent` | 25% | Yes (with 3) |
| 5 | Campaign Evaluation | `CampaignEvaluationAgent` | 40% | — |
| 6 | Insight Generation | `InsightGenerationAgent` | 55% | — |
| 7 | Recommendations | `RecommendationAgent` | 70% | — |
| 8 | Report Assembly | `ReportGenerationAgent` | 90% | — |

Parallel execution (stages 3+4):

```python
trend_result, anomaly_result = await asyncio.gather(
    self._trend_detection.run(TrendDetectionInput(records=records)),
    self._anomaly_detection.run(AnomalyDetectionInput(records=records)),
)
```

---

## Base Agent Pattern

**File:** `app/agents/base.py`

Every agent extends `BaseAgent[InputT, OutputT]`, which provides:

1. **Retry logic** — configurable `max_retries` per agent
2. **Timing instrumentation** — `time.monotonic()` elapsed tracking
3. **Structured logging** — agent name, attempt, elapsed_ms, success/failure
4. **Fallback hook** — overridable for graceful degradation

```python
class BaseAgent(ABC, Generic[InputT, OutputT]):
    name: str = "base_agent"
    max_retries: int = 1

    async def run(self, input_data: InputT) -> OutputT:
        for attempt in range(self.max_retries + 1):
            try:
                result = await self.execute(input_data)
                # log success with elapsed_ms
                return result
            except Exception:
                if attempt == self.max_retries:
                    return await self.fallback(input_data, last_error)
                # log warning, retry

    @abstractmethod
    async def execute(self, input_data: InputT) -> OutputT: ...

    async def fallback(self, input_data: InputT, error: Exception | None) -> OutputT:
        raise RuntimeError(f"Agent {self.name} failed: {error}")
```

### Retry Configuration

| Agent | max_retries | Reason |
|-------|:-----------:|--------|
| DataValidationAgent | 0 | Deterministic — retrying changes nothing |
| KPIComputationAgent | 1 | Pure math — unlikely to fail |
| TrendDetectionAgent | 1 | Pure math |
| AnomalyDetectionAgent | 1 | Pure math |
| CampaignEvaluationAgent | 1 | Pure math |
| InsightGenerationAgent | 2 | Claude API — network/rate-limit retries |
| RecommendationAgent | 2 | Claude API — network/rate-limit retries |
| ReportGenerationAgent | 1 | Assembly — should not fail |

---

## Stage 1: Data Validation

**Agent:** `DataValidationAgent`
**Skill:** `RawDataValidator`
**Input:** `list[MetricRecord]`
**Output:** `ValidationResult`

### What It Does

Validates every incoming metric record for completeness, correctness, and consistency before any computation runs.

### Validation Rules

| Rule | Check | Level |
|------|-------|-------|
| Required fields | `campaign_id`, `platform`, `date`, `organization_id` present | error |
| Non-negative values | `impressions >= 0`, `clicks >= 0`, `spend >= 0`, `conversions >= 0`, `conversion_value >= 0` | error |
| Cross-field consistency | `clicks <= impressions` (clicks can't exceed impressions) | warning |
| Cross-field consistency | `conversions <= clicks` (conversions can't exceed clicks) | warning |
| Spend-conversion coherence | If `spend > 0` then `impressions > 0` expected | warning |

### Output Schema

```python
class ValidationResult(BaseModel):
    total_records: int
    valid_records: int
    errors: list[ValidationIssue]       # block pipeline if critical
    warnings: list[ValidationIssue]     # log but continue

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def error_rate(self) -> float:
        return len(self.errors) / self.total_records if self.total_records > 0 else 0.0
```

### Pipeline Behavior

The pipeline proceeds even if validation finds errors — the `ValidationResult` is carried through to the final `PipelineResult` so consumers can inspect data quality. Individual records with errors are not filtered out at this stage to preserve completeness for downstream aggregation.

---

## Stage 2: KPI Computation

**Agent:** `KPIComputationAgent`
**Skills:** `KPIComputer`, `Aggregator`, `PeriodComparer`, `EfficiencyScorer`
**Input:** `list[MetricRecord]` + date range + comparison mode
**Output:** `KPIResult`

### What It Does

1. **Splits records** into current and previous periods
2. **Computes derived metrics** on every record (CTR, CPC, CPA, ROAS, CVR, CPM, AOV)
3. **Aggregates** into summary views (total, by-platform, by-campaign, daily)
4. **Compares** current vs. previous period (% change for all key metrics)

### Derived Metric Formulas

| Metric | Formula | Direction |
|--------|---------|-----------|
| CTR | `clicks / impressions × 100` | Higher is better |
| CPC | `spend / clicks` | Lower is better |
| CPA | `spend / conversions` | Lower is better |
| ROAS | `conversion_value / spend` | Higher is better |
| CVR | `conversions / clicks × 100` | Higher is better |
| CPM | `spend / impressions × 1000` | Lower is better |
| AOV | `conversion_value / conversions` | Higher is better |

All formulas use `safe_divide()` — returns `None` when denominator is zero.

### Period Comparison Logic

```python
# Previous period calculation
period_length = (date_range_end - date_range_start).days + 1

if comparison_period == "previous_year":
    prev_start = date_range_start.replace(year=year - 1)
    prev_end = prev_start + timedelta(days=period_length - 1)
else:  # "previous_period"
    prev_end = date_range_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_length - 1)
```

### PeriodComparison Fields

All deltas are computed via `pct_change(old, new) = ((new - old) / old) × 100`:

```
spend_change, spend_change_pct
impressions_change, impressions_change_pct
clicks_change, clicks_change_pct
conversions_change, conversions_change_pct
conversion_value_change, conversion_value_change_pct
roas_change_pct, cpa_change_pct, ctr_change_pct
```

### Aggregation Modes

| Mode | Method | Groups by |
|------|--------|-----------|
| Total | `aggregate_summary(records)` | All records → single `SummaryMetrics` |
| By platform | `aggregate_by(records, "platform")` | `meta_ads`, `google_ads`, etc. |
| By campaign | `aggregate_by(records, "campaign_id")` | Individual campaign UUIDs |

### Efficiency Scoring

The `EfficiencyScorer` computes a composite 0–1 score per campaign:

| Factor | Weight | Normalization |
|--------|:------:|---------------|
| ROAS | 35% | Percentile against all campaigns |
| CPA | 30% | Inverse percentile (lower = better) |
| CVR | 20% | Percentile |
| Volume (conversions) | 15% | Percentile |

```python
score = (roas_pct * 0.35) + (cpa_pct * 0.30) + (cvr_pct * 0.20) + (vol_pct * 0.15)
```

---

## Stage 3: Trend Detection

**Agent:** `TrendDetectionAgent`
**Skills:** `TrendClassifier`, `MovingAverageAnalyzer`, `PacingAnalyzer`, `SeasonalityDetector`
**Input:** `list[MetricRecord]` + optional budget + days_in_period
**Output:** `TrendAnalysis`
**Runs in parallel with:** Stage 4

### What It Does

1. **Classifies trend direction** for each metric via linear regression
2. **Computes moving averages** at multiple windows (7-day, 14-day, 28-day)
3. **Analyzes budget pacing** — on-track, underspending, or overspending
4. **Detects seasonality** (day-of-week patterns)

### Metrics Analyzed

```python
TREND_METRICS = ["spend", "impressions", "clicks", "conversions", "conversion_value"]
```

### Trend Classification Algorithm

Uses ordinary least squares (OLS) linear regression:

```python
def linear_regression(values: list[float]) -> tuple[float, float, float]:
    """Returns (slope, intercept, r_squared)."""
    n = len(values)
    x = range(n)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    # ... standard OLS calculation
    return slope, intercept, r_squared
```

**Direction mapping** (based on `normalized_slope_pct = slope / mean × 100`):

| Normalized Slope | R² | Direction |
|:----------------:|:--:|-----------|
| > +5% | > 0.5 | `ACCELERATING` |
| > +1% | any | `INCREASING` |
| -1% to +1% | any | `STABLE` |
| < -1% | any | `DECREASING` |
| < -5% | > 0.5 | `DECLINING` |

Minimum 7 data points required — fewer returns `INSUFFICIENT_DATA`.

### TrendResult Fields

```python
class TrendResult(BaseModel):
    metric: str                    # "spend", "conversions", etc.
    direction: TrendDirection      # ACCELERATING → DECLINING
    strength: float                # absolute r_squared
    slope: float                   # raw slope
    normalized_slope_pct: float    # slope / mean × 100
    r_squared: float               # regression fit quality
```

### Pacing Analysis

```python
class PacingAnalyzer:
    def analyze(actual_spend: list[float], budget: float, days_in_period: int) -> PacingResult:
        total_spent = sum(actual_spend)
        days_elapsed = len(actual_spend)
        expected_spent = budget * (days_elapsed / days_in_period)
        pacing_ratio = total_spent / expected_spent  # 1.0 = perfectly on track
        projected_total = (total_spent / days_elapsed) * days_in_period

        if pacing_ratio > 1.1:   status = "overspending"
        elif pacing_ratio < 0.9: status = "underspending"
        else:                    status = "on_track"
```

---

## Stage 4: Anomaly Detection

**Agent:** `AnomalyDetectionAgent`
**Skills:** `ZScoreDetector`, `ContextualDetector`, `CorrelationBreakDetector`, `MissingDataDetector`
**Input:** `list[MetricRecord]`
**Output:** `AnomalyAnalysis`
**Runs in parallel with:** Stage 3

### What It Does

Detects statistical outliers, contextual anomalies, broken metric correlations, and missing data gaps.

### Metrics Analyzed

```python
ANOMALY_METRICS = ["spend", "impressions", "clicks", "conversions", "conversion_value"]
```

### Detection Methods

#### 1. Z-Score Detection (requires > 30 data points)

```python
class ZScoreDetector:
    def detect(timeseries, metric_name, threshold=3.0, rolling_window=30, dates=None):
        for i in range(rolling_window, len(timeseries)):
            window = timeseries[i - rolling_window : i]
            mean = statistics.mean(window)
            stdev = statistics.stdev(window)
            if stdev > 0:
                z = (timeseries[i] - mean) / stdev
                if abs(z) > threshold:
                    anomaly_type = AnomalyType.SPIKE if z > 0 else AnomalyType.DROP
                    severity = classify_severity(abs(z), metric_name)
                    # create AnomalyPoint
```

**Severity classification** by z-score magnitude:

| Z-Score | Severity |
|:-------:|----------|
| >= 5.0 | `CRITICAL` |
| >= 4.0 | `HIGH` |
| >= 3.0 | `MEDIUM` |
| < 3.0 | `LOW` |

#### 2. Contextual Detection (requires >= 28 data points / 4 weeks)

Detects anomalies relative to same day-of-week historical pattern:

```python
class ContextualDetector:
    def detect(dated_values, metric_name, threshold=2.5):
        # Group values by day of week (0=Monday, 6=Sunday)
        by_dow: dict[int, list[float]] = defaultdict(list)
        for dv in dated_values:
            by_dow[dv.date.weekday()].append(dv.value)

        # For each value, compare to its day-of-week mean/stdev
        for dv in dated_values:
            dow_values = by_dow[dv.date.weekday()]
            mean = statistics.mean(dow_values)
            stdev = statistics.stdev(dow_values)
            z = (dv.value - mean) / stdev
            if abs(z) > threshold:
                # anomaly — unusual for this day of week
```

#### 3. Correlation Break Detection

Monitors expected correlations between metric pairs:

```python
EXPECTED_PAIRS = [
    ("impressions", "clicks"),        # more impressions → more clicks
    ("clicks", "conversions"),        # more clicks → more conversions
    ("spend", "impressions"),         # more spend → more impressions
]
```

Splits time series into first half and second half, computes Pearson correlation for each. If correlation drops significantly (e.g., from 0.9 to 0.2), flags a `CorrelationAnomaly`.

#### 4. Missing Data Detection

```python
class MissingDataDetector:
    def detect(dates_with_data, expected_start, expected_end) -> list[date]:
        all_expected = set()
        current = expected_start
        while current <= expected_end:
            all_expected.add(current)
            current += timedelta(days=1)
        return sorted(all_expected - set(dates_with_data))
```

### Deduplication & Sorting

Multiple detectors may flag the same (metric, date) — duplicates are removed, then sorted by severity:

```python
severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
unique_anomalies.sort(key=lambda a: severity_order.get(a.severity.value, 4))
```

### AnomalyPoint Fields

```python
class AnomalyPoint(BaseModel):
    metric: str                        # "spend", "clicks", etc.
    index: int                         # position in time series
    anomaly_date: Optional[date]       # actual date (if dates provided)
    value: float                       # observed value
    expected: Optional[float]          # rolling mean / dow mean
    z_score: Optional[float]           # how far from expected
    type: AnomalyType                  # SPIKE or DROP
    severity: Severity                 # CRITICAL → LOW
    deviation_pct: Optional[float]     # % deviation from expected
    context: Optional[str]             # "day_of_week" for contextual
```

---

## Stage 5: Campaign Evaluation

**Agent:** `CampaignEvaluationAgent`
**Skills:** `TierClassifier`, `BudgetAssessor`, `PlatformComparator`
**Input:** `KPIResult` (from Stage 2)
**Output:** `CampaignEvaluationResult`

### What It Does

1. **Classifies campaigns into 5 performance tiers** based on efficiency score percentile
2. **Assesses budget allocation** — identifies reallocation potential
3. **Compares platform performance** — rankings and efficiency

### Tier Classification

The `TierClassifier` computes an efficiency score per campaign (using `EfficiencyScorer` from Stage 2), then assigns tiers by percentile:

| Percentile | Tier | Meaning |
|:----------:|------|---------|
| >= 80th | `STAR` | Top performers |
| >= 60th | `STRONG` | Above average |
| >= 40th | `AVERAGE` | Middle of pack |
| >= 20th | `UNDERPERFORMER` | Below average |
| < 20th | `WASTER` | Budget drain |

Campaigns below `min_spend` threshold are excluded from classification.

**Algorithm:**

```python
class TierClassifier:
    def classify(self, records: list[MetricRecord]) -> dict[str, list[TieredCampaign]]:
        # 1. Aggregate metrics per campaign
        # 2. Compute benchmarks (median ROAS, CPA, CVR, volume)
        # 3. Score each campaign via EfficiencyScorer
        # 4. Rank by score → assign percentile → map to tier
        # 5. Return dict: {"star": [...], "strong": [...], ...}
```

### Budget Assessment

```python
class BudgetAssessor:
    def assess(self, tiered: dict[str, list[TieredCampaign]]) -> BudgetAssessment:
        # Calculate spend per tier
        # reallocation_potential = spend on underperformers + wasters
        # is_well_allocated = reallocation_potential < 15% of total spend
```

### Platform Comparison

```python
class PlatformComparator:
    def compare(self, by_platform: dict[str, SummaryMetrics]) -> dict:
        # Returns: { rankings: {...}, most_efficient: str, highest_volume: str }
```

### TieredCampaign Fields

```python
class TieredCampaign(BaseModel):
    campaign_id: uuid.UUID
    campaign_name: str
    platform: str
    tier: CampaignTier              # STAR → WASTER
    efficiency_score: float         # 0.0 → 1.0
    percentile: float               # 0.0 → 1.0
    spend: float
    roas: Optional[float]
    cpa: Optional[float]
    conversions: int
```

---

## Stage 6: Insight Generation

**Agent:** `InsightGenerationAgent`
**Skills:** `InsightPromptBuilder`, `InsightParser`, `TemplateFallback`
**External:** Claude API (Anthropic)
**Input:** KPIs + Trends + Anomalies + Evaluation + tone + ai_model
**Output:** `InsightGenerationResult`

### What It Does

1. **Builds a structured prompt** from all upstream pipeline data
2. **Calls Claude API** to generate insights + executive summary
3. **Parses AI response** into typed `GeneratedInsight` objects
4. **Falls back to templates** if Claude API is unavailable or fails

### Prompt Architecture

The `InsightPromptBuilder` constructs three prompts:

#### System Prompt

Sets the AI persona based on tone:

| Tone | Persona |
|------|---------|
| `executive` | Senior marketing strategist writing for C-level executives |
| `detailed` | Data analyst providing thorough technical analysis |
| `casual` | Marketing team lead giving a friendly debrief |

#### Data Context

Structured text block injected into both insight and summary prompts:

```
## Performance Summary
- Total Spend: $45,230 (▲ 8.2%)
- Conversions: 1,820 (▲ 12.5%)
- ROAS: 4.03x (▲ 3.1%)
...

## Trends
- spend: INCREASING (strength: 0.85, slope: +2.3%/day)
- conversions: ACCELERATING (strength: 0.92, slope: +3.1%/day)
...

## Anomalies
- SPIKE in spend on 2026-02-18 (z-score: 4.2, $3,420 vs expected $980)
...

## Campaign Tiers
Stars: Summer Sale Retargeting (ROAS 5.2x), Holiday Promo (ROAS 4.8x)
Wasters: Display Prospecting (ROAS 0.7x, $3,100 spent)
...
```

#### Insight Prompt

Asks Claude to generate 3-7 insights as JSON array:

```
Analyze the data and generate insights as a JSON array. Each insight must have:
- category: performance | efficiency | anomaly | opportunity | risk
- sentiment: positive | neutral | attention_needed
- priority: 1-5 (1 = highest)
- headline: concise finding (< 80 chars)
- detail: 1-2 sentence explanation with specific numbers
- confidence: 0.0-1.0
```

#### Executive Summary Prompt

```
Write a 2-3 paragraph executive summary covering:
1. Overall performance vs. prior period
2. Key wins and risks
3. Forward-looking outlook
```

### AI Response Parsing

`InsightParser` extracts JSON from Claude's response, handling common edge cases:

```python
class InsightParser:
    def parse_insights(self, insight_text: str) -> list[GeneratedInsight]:
        # 1. Try to extract JSON array from markdown code blocks (```json...```)
        # 2. Try to parse raw text as JSON array
        # 3. Validate each insight has required fields
        # 4. Map string enums to InsightCategory/InsightSentiment
        # 5. Return list of GeneratedInsight
```

### Template Fallback

When Claude API is unavailable (`anthropic_client=None`) or all retries fail, `TemplateFallback` generates rule-based insights from the structured data:

```python
class TemplateFallback:
    TEMPLATES = {
        "roas_improvement": "ROAS improved to {roas}x from {prev_roas}x...",
        "conversion_growth": "Conversions grew {pct}% to {total}...",
        "cpa_reduction": "CPA decreased by {pct}% to ${cpa}...",
        "waster_alert": "${spend} allocated to campaigns with ROAS below 1.0x...",
        "anomaly_detected": "Unusual {type} in {metric} on {date}...",
        "budget_opportunity": "Top campaigns have {roas}x ROAS with only {pct}% of budget...",
    }

    def generate_fallback_insights(self, kpis, evaluation) -> list[GeneratedInsight]:
        # 1. Check each template condition against actual data
        # 2. Generate insights for conditions that match
        # 3. Return 3-6 template-based insights
```

**Fallback also provides a default executive summary:**
```
"Report insights generated using template analysis."
```

### InsightGenerationResult Fields

```python
class InsightGenerationResult(BaseModel):
    insights: list[GeneratedInsight]   # 3-7 insights
    executive_summary: str             # 2-3 paragraph narrative
    ai_model: str                      # "claude-sonnet-4-6" or "template_fallback"
    tokens_used: int                   # 0 if fallback
```

---

## Stage 7: Recommendation Generation

**Agent:** `RecommendationAgent`
**Skills:** `InsightPromptBuilder`, `InsightParser`
**External:** Claude API (Anthropic)
**Input:** KPIs + Trends + Anomalies + Evaluation + Insights + tone + ai_model
**Output:** `RecommendationResult`

### What It Does

1. **Builds a recommendation prompt** using the same data context as Stage 6 plus the generated insights
2. **Calls Claude API** to generate actionable recommendations
3. **Parses and validates** AI response into `GeneratedRecommendation` objects
4. **Falls back to template recommendations** on failure

### Prompt Structure

The recommendation prompt includes insights from Stage 6 as additional context:

```
Based on the data analysis and these insights:
{insights_json}

Generate 3-5 actionable recommendations as a JSON array. Each must have:
- category: budget | targeting | creative | bidding | scheduling
- priority: critical | high | medium | low
- title: concise action (< 100 chars)
- description: 1-2 sentence explanation
- expected_impact: quantified impact estimate
- effort: low | medium | high
- action_items: list of 2-4 specific steps
```

### Response Parsing

```python
@staticmethod
def _parse_recs(raw_recs: list[dict]) -> list[GeneratedRecommendation]:
    # For each raw recommendation:
    # 1. Validate required fields (title, description present)
    # 2. Safely map category enum (default to BUDGET if invalid)
    # 3. Extract effort, priority, action_items with defaults
    # 4. Return list[GeneratedRecommendation]
```

### Template Fallback

Generates rule-based recommendations from pipeline data:

```python
@staticmethod
def _generate_template_recs(input_data) -> list[GeneratedRecommendation]:
    recs = []

    # 1. Budget reallocation (if wasters exist)
    if evaluation.bottom_performers:
        waster_spend = sum(c.spend for c in evaluation.bottom_performers)
        recs.append(GeneratedRecommendation(
            category="budget", priority="high",
            title="Reallocate budget from underperforming campaigns",
            description=f"${waster_spend:,.2f} is allocated to underperforming campaigns...",
            action_items=["Review underperforming campaigns",
                          "Pause campaigns with ROAS < 1.0x", ...]
        ))

    # 2. Trend-based (if conversions declining)
    for trend in trends:
        if trend.direction in ("decreasing", "declining") and trend.metric == "conversions":
            recs.append(...)

    # 3. Default stable recommendation if none generated
    if not recs:
        recs.append(GeneratedRecommendation(
            category="budget", priority="medium",
            title="Maintain current strategy with incremental optimization",
            ...
        ))

    return recs
```

### GeneratedRecommendation Fields

```python
class GeneratedRecommendation(BaseModel):
    category: RecommendationCategory   # BUDGET | TARGETING | CREATIVE | BIDDING | SCHEDULING
    priority: str                      # critical | high | medium | low
    title: str
    description: str
    expected_impact: str               # "Estimated +$12,400 revenue"
    estimated_impact_value: Optional[float]
    effort: str                        # low | medium | high
    action_items: list[str]            # 2-4 specific steps
    campaign_id: Optional[uuid.UUID]
    platform: Optional[str]
```

---

## Stage 8: Report Assembly

**Agent:** `ReportGenerationAgent`
**Skills:** None (pure assembly)
**Input:** All outputs from stages 1-7
**Output:** `PipelineResult`

### What It Does

1. **Aggregates token usage** from insight + recommendation stages
2. **Estimates AI cost** based on model pricing
3. **Assembles final `PipelineResult`** containing all pipeline outputs
4. **Logs completion** with summary statistics

### Cost Estimation

```python
COSTS_PER_1K_TOKENS = {
    "claude-sonnet-4-6": 0.009,     # $9 per million tokens (blended)
    "claude-opus-4-6": 0.045,       # $45 per million tokens (blended)
}

def _estimate_cost(tokens: int, model: str) -> float:
    rate = COSTS_PER_1K_TOKENS.get(model, 0.009)
    return (tokens / 1000) * rate
```

### PipelineResult Fields

```python
class PipelineResult(BaseModel):
    report_id: uuid.UUID
    validation: ValidationResult           # Stage 1
    kpis: KPIResult                        # Stage 2
    trends: TrendAnalysis                  # Stage 3
    anomalies: AnomalyAnalysis             # Stage 4
    campaign_evaluation: CampaignEvaluationResult  # Stage 5
    insights: InsightGenerationResult      # Stage 6
    recommendations: RecommendationResult  # Stage 7
    total_tokens_used: int                 # Stages 6+7
    total_ai_cost: float                   # Estimated USD
```

---

## Data Contracts

### Pipeline Input

```python
class ReportRequest(BaseModel):
    report_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    organization_id: uuid.UUID
    generated_by: uuid.UUID
    date_range_start: date
    date_range_end: date
    comparison_period: str = "previous_period"   # previous_period | previous_year
    platforms: list[str]                         # ["meta_ads", "google_ads"]
    tone: str = "executive"                      # executive | detailed | casual
    ai_model: str = "claude-sonnet-4-6"
    title: str = ""
    template: str = "monthly_performance"

class MetricRecord(BaseModel):
    campaign_id: uuid.UUID
    campaign_name: str = ""
    platform: str
    date: date
    organization_id: uuid.UUID
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    conversions: int = 0
    conversion_value: float = 0.0
    # Derived (computed by KPIComputer):
    ctr: Optional[float] = None
    cpc: Optional[float] = None
    cpa: Optional[float] = None
    roas: Optional[float] = None
    cvr: Optional[float] = None
    cpm: Optional[float] = None
    aov: Optional[float] = None
```

### Inter-Stage Data Flow

```
MetricRecord[] ──┬──→ Stage 1 ──→ ValidationResult
                 │
                 ├──→ Stage 2 ──→ KPIResult
                 │                    │
                 ├──→ Stage 3 ──→ TrendAnalysis          ─┐
                 │                                         │
                 └──→ Stage 4 ──→ AnomalyAnalysis         ─┤
                                                           │
                      KPIResult ──→ Stage 5 ──→ CampaignEvaluationResult
                                                           │
                      KPIs + Trends + Anomalies           ─┤
                      + Evaluation + tone ──→ Stage 6 ──→ InsightGenerationResult
                                                           │
                      All above + Insights ──→ Stage 7 ──→ RecommendationResult
                                                           │
                      All outputs ──→ Stage 8 ──→ PipelineResult
```

---

## Agent → Skill Dependency Map

```
┌───────────────────────────┐     ┌──────────────────────────────────┐
│         AGENTS            │     │            SKILLS                │
├───────────────────────────┤     ├──────────────────────────────────┤
│                           │     │                                  │
│  DataValidationAgent ─────┼────▶│  RawDataValidator                │
│                           │     │                                  │
│  KPIComputationAgent ─────┼────▶│  KPIComputer                     │
│                           │────▶│  Aggregator                      │
│                           │────▶│  PeriodComparer                  │
│                           │────▶│  EfficiencyScorer                │
│                           │     │                                  │
│  TrendDetectionAgent ─────┼────▶│  TrendClassifier                 │
│                           │────▶│  MovingAverageAnalyzer            │
│                           │────▶│  PacingAnalyzer                  │
│                           │────▶│  SeasonalityDetector              │
│                           │     │                                  │
│  AnomalyDetectionAgent ──┼────▶│  ZScoreDetector                   │
│                           │────▶│  ContextualDetector               │
│                           │────▶│  CorrelationBreakDetector         │
│                           │────▶│  MissingDataDetector              │
│                           │     │                                  │
│  CampaignEvaluationAgent ┼────▶│  TierClassifier                   │
│                           │────▶│  BudgetAssessor                   │
│                           │────▶│  PlatformComparator               │
│                           │     │                                  │
│  InsightGenerationAgent ──┼────▶│  InsightPromptBuilder             │
│                           │────▶│  InsightParser                    │
│                           │────▶│  TemplateFallback                 │
│                           │────▶│  Claude API (external)            │
│                           │     │                                  │
│  RecommendationAgent ─────┼────▶│  InsightPromptBuilder             │
│                           │────▶│  InsightParser                    │
│                           │────▶│  Claude API (external)            │
│                           │     │                                  │
│  ReportGenerationAgent ───┼────▶│  (no skills — pure assembly)     │
│                           │     │                                  │
└───────────────────────────┘     └──────────────────────────────────┘
```

### Shared Skill Layer

The `SemanticMetricLayer` is the single source of truth for all metric definitions, formatters, and benchmarks. It is not used directly by agents, but underpins the vocabulary used across all skills:

| Metric | ID | Format | Direction | Aggregation |
|--------|----|--------|-----------|-------------|
| Impressions | `impressions` | `integer_comma` | higher_is_better | sum |
| Clicks | `clicks` | `integer_comma` | higher_is_better | sum |
| Spend | `spend` | `currency_2dp` | neutral | sum |
| Conversions | `conversions` | `integer_comma` | higher_is_better | sum |
| Conv. Value | `conversion_value` | `currency_2dp` | higher_is_better | sum |
| CTR | `ctr` | `percentage_2dp` | higher_is_better | weighted avg |
| CPC | `cpc` | `currency_2dp` | lower_is_better | weighted avg |
| CPA | `cpa` | `currency_2dp` | lower_is_better | weighted avg |
| ROAS | `roas` | `ratio_2dp` | higher_is_better | weighted avg |
| CVR | `cvr` | `percentage_2dp` | higher_is_better | weighted avg |
| CPM | `cpm` | `currency_2dp` | lower_is_better | weighted avg |
| AOV | `aov` | `currency_2dp` | higher_is_better | weighted avg |

---

## Fallback Strategy

The pipeline is designed to **always produce output**, even when external services fail:

| Failure | Impact | Fallback |
|---------|--------|----------|
| Claude API down | No AI insights | `TemplateFallback.generate_fallback_insights()` — rule-based insights from KPIs and tier data |
| Claude API rate-limited | Delayed insights | 2 retries with backoff, then template fallback |
| Claude returns unparseable JSON | Garbled insights | `InsightParser` attempts multiple extraction strategies; falls back to templates |
| No `anthropic_client` provided | Testing mode | Template fallback used automatically — pipeline still returns valid `PipelineResult` |
| Stage 1-5 exception | Agent crash | `BaseAgent.run()` retries once, then raises (these are deterministic — failures indicate bad data, not transient issues) |

### AI Model Selection

| Model | Use Case | Cost | Quality |
|-------|----------|------|---------|
| `claude-sonnet-4-6` | Standard reports | ~$0.009/1K tokens | Good |
| `claude-opus-4-6` | Premium reports | ~$0.045/1K tokens | Best |
| `template_fallback` | No AI available | $0 | Structured but generic |

---

## Testing

**File:** `backend/tests/test_pipeline.py`
**Total tests:** 23

### Test Coverage

| Test Class | Tests | What's Covered |
|-----------|:-----:|----------------|
| `TestSemanticMetricLayer` | 5 | get_metric, format_value, format_none, unknown_metric, list_metrics |
| `TestKPIComputation` | 3 | safe_divide, compute_derived, aggregate_summary |
| `TestTrendDetection` | 4 | linear_regression, trend_classification, stable_trend, insufficient_data |
| `TestAnomalyDetection` | 2 | zscore_detection (with spike), no_anomalies (smooth trend) |
| `TestDataValidation` | 2 | valid_records, negative_spend_rejection |
| `TestCampaignEvaluation` | 1 | tier_classification with 10 campaigns |
| `TestAgents` | 5 | Each agent (1-5) runs end-to-end with synthetic data |
| `TestPipelineOrchestrator` | 1 | Full pipeline without AI (template fallback) |

### Synthetic Data Generator

```python
def _make_records(num_days=60, num_campaigns=5, start_date=None) -> list[MetricRecord]:
    """
    Generates realistic synthetic data:
    - Slight upward trend in spend (base_spend = 100 + day_offset * 0.5)
    - Proportional impressions, clicks, conversions
    - Day-of-week variation (day_offset % 7 * 5)
    - Multiple campaigns across meta_ads and google_ads platforms
    """
```

### Running Tests

```bash
cd backend
python -m pytest tests/test_pipeline.py -v
# 23 passed
```

---

## Performance Characteristics

| Stage | Computation | Typical Duration | Bottleneck |
|-------|-------------|:----------------:|------------|
| 1. Data Validation | O(n) scan | < 50ms | — |
| 2. KPI Computation | O(n) aggregation | < 100ms | — |
| 3. Trend Detection | O(n × m) regression | < 200ms | — |
| 4. Anomaly Detection | O(n × m) z-score windows | < 200ms | — |
| 5. Campaign Evaluation | O(c log c) sort + percentile | < 100ms | — |
| 6. Insight Generation | Claude API call | 5-15s | **Network + LLM inference** |
| 7. Recommendations | Claude API call | 5-15s | **Network + LLM inference** |
| 8. Report Assembly | O(1) composition | < 10ms | — |

**Total without AI:** < 1 second
**Total with AI (Sonnet):** 10-30 seconds
**Total with AI (Opus):** 15-45 seconds

The parallel execution of stages 3+4 saves approximately 200ms compared to sequential execution.

---

## Persistence Flow (Post-Pipeline)

After the pipeline completes inside the Celery task, results are persisted:

```python
async def _persist_results(db: AsyncSession, report: Report, result: PipelineResult):
    # 1. Persist insights
    for i, insight in enumerate(result.insights.insights):
        db.add(Insight(
            report_id=report.id,
            organization_id=report.organization_id,
            category=insight.category.value,
            severity=insight.sentiment.value,
            title=insight.headline,
            description=insight.detail,
            supporting_data=insight.supporting_data,
            confidence_score=insight.confidence,
            platform=insight.platform,
            sort_order=i,
        ))

    # 2. Persist recommendations
    for i, rec in enumerate(result.recommendations.recommendations):
        db.add(Recommendation(
            report_id=report.id,
            organization_id=report.organization_id,
            category=rec.category.value,
            priority=rec.priority,
            title=rec.title,
            description=rec.description,
            expected_impact=rec.expected_impact,
            effort=rec.effort,
            action_items=rec.action_items,
            sort_order=i,
        ))

    # 3. Update report
    report.status = "completed"
    report.summary_data = {
        "executive_summary": result.insights.executive_summary,
        "kpi_summary": result.kpis.current_period.model_dump(),
        "comparison": result.kpis.comparison.model_dump() if result.kpis.comparison else None,
        "total_anomalies": len(result.anomalies.point_anomalies),
        "tier_distribution": {
            tier: len(campaigns)
            for tier, campaigns in result.campaign_evaluation.tiered_campaigns.items()
        },
    }
    report.ai_model = result.insights.ai_model
    report.ai_tokens_used = result.total_tokens_used
    report.generation_time_ms = elapsed_ms

    await db.commit()
```
