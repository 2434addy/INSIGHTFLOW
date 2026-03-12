# InsightFlow — System Architecture Overview

> **Version:** 1.0
> **Last Updated:** 2026-03-12
> **Status:** Architecture complete — MVP build pending

---

## 1. What Is InsightFlow?

InsightFlow is an AI-powered SaaS platform that eliminates the 5–10 hours per week marketing agencies spend manually building client reports. It connects to ad platforms (Meta Ads, Google Ads, GA4, Shopify), runs an 8-stage analytics pipeline, and delivers client-ready performance reports with AI-generated insights and recommendations.

**Target Users:**

| Persona | Role | Primary Use |
|---------|------|-------------|
| Agency Owner | Strategic oversight | Monitor all clients, team performance |
| Account Manager | Day-to-day client work | Generate and deliver client reports |
| Marketing Analyst | Data analysis | Investigate trends, anomalies, optimizations |
| Client Stakeholder | Report consumer | View read-only branded reports |

---

## 2. System Architecture — Bird's Eye View

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENTS                                       │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────┐                    │
│  │ Browser  │   │ Client Portal│   │ PDF Export   │                    │
│  │ (Next.js)│   │ (read-only)  │   │ (S3-hosted)  │                    │
│  └────┬─────┘   └──────┬───────┘   └──────────────┘                    │
│       │                │                                                │
├───────┼────────────────┼────────────────────────────────────────────────┤
│       │     CloudFlare CDN / WAF                                        │
├───────┼────────────────┼────────────────────────────────────────────────┤
│       │                │                                                │
│  ┌────▼────────────────▼─────┐       ┌──────────────────────────┐      │
│  │       FastAPI Server      │       │     Celery Workers       │      │
│  │  ┌─────────────────────┐  │       │  ┌────────────────────┐  │      │
│  │  │ API Endpoints       │  │       │  │ Report Generation  │  │      │
│  │  │ Middleware Stack     │◄─┼───────┼─►│ Data Ingestion     │  │      │
│  │  │ Auth / RBAC          │  │ Redis │  │ Maintenance Tasks  │  │      │
│  │  │ Service Layer        │  │(broker│  └────────┬───────────┘  │      │
│  │  │ Repository Layer     │  │+cache)│           │              │      │
│  │  └─────────┬───────────┘  │       └───────────┼──────────────┘      │
│  └────────────┼──────────────┘                   │                     │
│               │                                   │                     │
│  ┌────────────▼───────────────────────────────────▼──────────────┐      │
│  │                    PostgreSQL 16 (RDS)                         │      │
│  │  Users · Organizations · Campaigns · Metrics · Reports        │      │
│  │  Row-Level Security · Partitioned Metrics                     │      │
│  └───────────────────────────────────────────────────────────────┘      │
│                                                                         │
│  ┌────────────────┐  ┌──────────────────┐  ┌──────────────────────┐    │
│  │  Claude API    │  │  Platform APIs   │  │  AWS S3              │    │
│  │  (Anthropic)   │  │  Meta · Google   │  │  (PDF reports)       │    │
│  │  Insights +    │  │  GA4 · Shopify   │  │                      │    │
│  │  Recommendations│ │                  │  │                      │    │
│  └────────────────┘  └──────────────────┘  └──────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. User Flow

### 3.1 First-Time User Journey

```
┌──────────┐    ┌──────────────┐    ┌────────────────┐    ┌──────────────┐
│ Register │───►│ Onboarding   │───►│ Connect        │───►│ First Report │
│ Account  │    │ Wizard       │    │ Ad Platform    │    │ Generated    │
└──────────┘    └──────────────┘    └────────────────┘    └──────────────┘
     │                │                     │                     │
     ▼                ▼                     ▼                     ▼
  Create user    Set up workspace     OAuth connect to       Pipeline runs,
  + organization  name, invite team   Meta/Google/etc.      AI insights appear
```

**Goal: platform connected → first report in under 30 minutes.**

### 3.2 Returning User Flow

```
┌─────────┐    ┌──────────────┐    ┌──────────────────┐
│  Login  │───►│  Dashboard   │───►│  Generate Report │
└─────────┘    │  (KPIs +     │    │  or View Insights│
               │   Campaigns) │    └──────────────────┘
               └──────┬───────┘
                      │
          ┌───────────┼────────────┐
          ▼           ▼            ▼
    View Insights  Campaign     Client
    & Anomalies    Deep-Dive    Portal
```

### 3.3 Report Delivery Flow

```
User clicks "Generate Report"
    │
    ▼
Configure: date range, platforms, tone, AI model
    │
    ▼
POST /v1/reports/generate → 202 Accepted
    │
    ├─── Client polls GET /v1/reports/{id}/progress
    │    (shows 8-stage pipeline stepper in UI)
    │
    ▼
Report ready → View in browser / Download PDF / Share client link
```

---

## 4. Data Ingestion Layer

The ingestion layer syncs marketing data from external ad platforms into InsightFlow's unified database on an hourly schedule.

### 4.1 Architecture

```
                    Celery Beat (hourly)
                          │
                          ▼
              sync_all_connections task
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
         sync_data     sync_data   sync_data
         (Meta Ads)   (Google Ads) (Shopify)
              │           │           │
              ▼           ▼           ▼
     ┌────────────────────────────────────────┐
     │        Platform Connector Layer         │
     │                                        │
     │  BaseConnector (abstract)              │
     │  ├─ Rate limiting (token bucket)       │
     │  ├─ Exponential backoff (3 retries)    │
     │  ├─ Circuit breaker (5-fail → open)    │
     │  └─ OAuth token refresh + encryption   │
     │                                        │
     │  Concrete: MetaAdsConnector            │
     │            GoogleAdsConnector           │
     │            GoogleAnalyticsConnector     │
     │            ShopifyConnector             │
     └────────────────┬───────────────────────┘
                      │
                      ▼
     ┌────────────────────────────────────────┐
     │        Metrics Normalizer              │
     │                                        │
     │  Raw platform data → Unified schema    │
     │  ├─ Standardize field names            │
     │  ├─ Compute derived metrics (CTR,      │
     │  │   CPC, CPA, ROAS, CVR, CPM, AOV)   │
     │  ├─ Validate ranges + required fields  │
     │  └─ Track rejection reasons            │
     └────────────────┬───────────────────────┘
                      │
                      ▼
     ┌────────────────────────────────────────┐
     │         PostgreSQL (Metrics table)      │
     │  Upsert key: campaign_id + date +      │
     │               platform + granularity    │
     │  Partitioned by month for query perf    │
     └────────────────────────────────────────┘
```

### 4.2 Supported Platforms

| Platform | Data Pulled | Granularity |
|----------|-------------|-------------|
| **Meta Ads** | Campaigns, ad sets, ads, spend, impressions, clicks, conversions | Daily |
| **Google Ads** | Search/display/shopping/PMax campaigns, cost, clicks, conversions | Daily |
| **Google Analytics (GA4)** | Traffic sources, conversions, audience data | Daily |
| **Shopify** | Revenue, orders, AOV, products, conversion value | Daily |

### 4.3 Resilience Patterns

| Pattern | Behavior |
|---------|----------|
| **Rate Limiting** | Token-bucket limiter per connector, respects platform quotas |
| **Exponential Backoff** | 3 retries with 2^attempt delay on transient failures |
| **Circuit Breaker** | CLOSED → OPEN (after 5 failures) → HALF_OPEN → CLOSED |
| **Token Encryption** | AES-256-GCM envelope encryption for stored OAuth tokens |
| **Upsert** | Idempotent writes — re-syncing the same date range never duplicates data |

### 4.4 Events Emitted

- **`DataSyncCompleted`** — triggers cache invalidation, UI refresh
- **`DataSyncFailed`** — triggers user notification, health monitoring alerts

---

## 5. Analytics Pipeline

The pipeline transforms raw metrics into structured analysis through 8 stages orchestrated as a DAG (Directed Acyclic Graph). Stages 3 and 4 run in parallel for maximum throughput.

### 5.1 Pipeline DAG

```
        ┌──────────────────────────────┐
        │  MetricRecord[] (raw input)  │
        └──────────────┬───────────────┘
                       │
              ┌────────▼─────────┐
              │  1. VALIDATION   │  Validate completeness, types, ranges
              │  DataValidation  │  Output: ValidationResult
              │  Agent           │  (errors, warnings, valid count)
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │  2. KPI          │  Compute CTR, CPC, CPA, ROAS, CVR
              │  COMPUTATION     │  Aggregate by platform, campaign
              │                  │  Compare vs previous period
              │                  │  Output: KPIResult
              └────────┬─────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
  ┌────────▼─────────┐   ┌────────▼─────────┐
  │  3. TREND        │   │  4. ANOMALY      │    ← parallel execution
  │  DETECTION       │   │  DETECTION       │      via asyncio.gather()
  │                  │   │                  │
  │  OLS regression  │   │  Z-score         │
  │  Moving averages │   │  Contextual      │
  │  Pacing analysis │   │  Correlation     │
  │                  │   │  Missing data    │
  │  Output:         │   │  Output:         │
  │  TrendAnalysis   │   │  AnomalyAnalysis │
  └────────┬─────────┘   └────────┬─────────┘
           │                       │
           └───────────┬───────────┘
                       │
              ┌────────▼─────────┐
              │  5. CAMPAIGN     │  Classify into 5 tiers:
              │  EVALUATION      │  Star · Strong · Average
              │                  │  Underperformer · Waster
              │                  │  Budget allocation assessment
              │                  │  Cross-platform comparison
              │                  │  Output: CampaignEvaluationResult
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │  6. INSIGHT      │  Claude API call with full context
              │  GENERATION      │  Produces executive summary +
              │                  │  categorized insights (performance,
              │                  │  efficiency, growth, anomaly,
              │  ☁ Claude API    │  opportunity, risk)
              │                  │  Fallback: template-based insights
              │                  │  Output: InsightGenerationResult
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │  7. RECOMMEND-   │  Claude API call for actionable
              │  ATION           │  optimization recommendations
              │  GENERATION      │  (budget, targeting, creative,
              │                  │  bidding, scheduling)
              │  ☁ Claude API    │  Priority + effort + impact scoring
              │                  │  Fallback: template recommendations
              │                  │  Output: RecommendationResult
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │  8. REPORT       │  Assemble all stage outputs
              │  ASSEMBLY        │  Compute total token usage + cost
              │                  │  Output: PipelineResult
              └────────┬─────────┘
                       │
              ┌────────▼─────────────────────┐
              │       PipelineResult          │
              │  ├─ validation                │
              │  ├─ kpis (current + previous) │
              │  ├─ trends                    │
              │  ├─ anomalies                 │
              │  ├─ campaign_evaluation       │
              │  ├─ insights + exec summary   │
              │  ├─ recommendations           │
              │  ├─ total_tokens_used         │
              │  └─ total_ai_cost             │
              └──────────────────────────────┘
```

### 5.2 Agent → Skill Architecture

Agents **orchestrate**. Skills **compute**. This separation keeps domain logic reusable and testable.

```
┌──────────────────────────────────────────────────────────────┐
│                         AGENTS                                │
│  (orchestration, retry logic, error handling, fallbacks)      │
│                                                               │
│  DataValidationAgent ──────► DataQualityValidation (skill)    │
│  KPIComputationAgent ──────► KPIComputation + MetricLayer     │
│  TrendDetectionAgent ──────► TrendDetection (skill)           │
│  AnomalyDetectionAgent ───► AnomalyDetection (skill)         │
│  CampaignEvaluationAgent ─► CampaignEvaluation + MetricLayer │
│  InsightGenerationAgent ──► InsightSummarization (skill)      │
│  RecommendationAgent ─────► InsightSummarization (skill)      │
│  ReportGenerationAgent ───► (assembler — no skills)           │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                          SKILLS                               │
│  (stateless, pure functions, no DB access, fully testable)    │
│                                                               │
│  Atomic:     SemanticMetricLayer · KPIComputation             │
│              TrendDetection · AnomalyDetection                │
│              CampaignEvaluation · DataQualityValidation       │
│                                                               │
│  Composite:  InsightSummarization · VisualizationRendering    │
│                                                               │
│  Workflow:   ReportGeneration (pipeline orchestrator)          │
└──────────────────────────────────────────────────────────────┘
```

### 5.3 Pipeline Execution Infrastructure

| Component | Purpose |
|-----------|---------|
| **PipelineOrchestrator** | Coordinates all 8 stages in DAG dependency order |
| **PipelineContext** | Immutable shared context (report config, AI client, progress callback) |
| **PipelineState** | Stage state machine (PENDING → RUNNING → COMPLETED/FAILED) for tracking and resumability |
| **Stage Executors** | Thin wrappers in `pipeline/stages/` that connect orchestrator to agents |

### 5.4 Performance Characteristics

| Scenario | Duration |
|----------|----------|
| Stages 1–5 (pure computation) | < 1 second |
| With Claude Sonnet (stages 6–7) | 10–30 seconds |
| With Claude Opus (premium reports) | 15–45 seconds |
| Pipeline timeout | 5 minutes (configurable) |
| Max input records | 50,000 (safety limit) |

---

## 6. AI Insight Generation

Stages 6 and 7 of the pipeline use the Claude API (Anthropic) to transform structured analytics data into natural language insights and actionable recommendations.

### 6.1 Insight Generation (Stage 6)

```
┌─────────────────────────────────────────────────┐
│                  INPUT                           │
│  KPIResult + TrendAnalysis + AnomalyAnalysis    │
│  + CampaignEvaluationResult + tone + ai_model   │
└─────────────────────┬───────────────────────────┘
                      │
           ┌──────────▼──────────┐
           │ InsightPromptBuilder │  Build structured prompt with
           │ (skill)              │  data summaries, trend context,
           │                      │  anomaly highlights, tier results
           └──────────┬──────────┘
                      │
           ┌──────────▼──────────┐
           │   Claude API Call    │  Model: claude-sonnet-4-6 (standard)
           │   (2 retries)        │         claude-opus-4-6 (premium)
           │                      │  Max tokens: 4,096
           │                      │  Timeout: 120 seconds
           └──────────┬──────────┘
                      │
                  ┌───┴───┐
              Success?  Failure?
                  │         │
                  ▼         ▼
           ┌──────────┐  ┌────────────────┐
           │ Parse AI  │  │ Template       │
           │ Response  │  │ Fallback       │
           │           │  │ (rule-based    │
           │ Extract:  │  │  insights from │
           │ • Summary │  │  data patterns)│
           │ • Insights│  │                │
           └──────────┘  └────────────────┘
                  │              │
                  └──────┬───────┘
                         ▼
              InsightGenerationResult
              ├─ executive_summary (2–3 paragraphs)
              ├─ insights[] (categorized, prioritized)
              │   ├─ category: performance|efficiency|growth|anomaly|opportunity|risk
              │   ├─ sentiment: positive|neutral|attention_needed
              │   ├─ priority: 1–5
              │   ├─ headline + detail
              │   ├─ supporting_data
              │   └─ confidence: 0.0–1.0
              ├─ ai_model used
              └─ tokens_used
```

### 6.2 Recommendation Generation (Stage 7)

```
Same architecture as Stage 6, but generates:

RecommendationResult
├─ recommendations[]
│   ├─ category: budget|targeting|creative|bidding|scheduling
│   ├─ priority: critical|high|medium|low
│   ├─ title + description
│   ├─ expected_impact (text) + estimated_impact_value ($)
│   ├─ effort: low|medium|high
│   ├─ action_items[] (step-by-step checklist)
│   ├─ campaign_id (if campaign-specific)
│   └─ platform (if platform-specific)
├─ ai_model used
└─ tokens_used
```

### 6.3 Fallback Strategy

When Claude API calls fail (timeout, rate limit, network error), both stages fall back to template-based generation:

| Fallback Source | Generated From |
|-----------------|----------------|
| Trend insights | Regression slopes + direction classifications |
| Anomaly alerts | Z-score severity + deviation percentages |
| Tier recommendations | Campaign tier (waster → pause, star → scale) |
| Budget insights | Allocation assessment + reallocation potential |
| Pacing alerts | Overspending/underspending ratios |

**Design guarantee:** A report is always generated, even without AI connectivity.

### 6.4 AI Cost Management

| Model | Input Cost | Output Cost | Typical Report |
|-------|-----------|-------------|----------------|
| Claude Sonnet | $3/M tokens | $15/M tokens | ~$0.05–0.15 |
| Claude Opus | $15/M tokens | $75/M tokens | ~$0.25–0.75 |

- Token usage tracked per stage and accumulated in PipelineContext
- Total cost stored in PipelineResult for billing
- Premium model (Opus) available as paid upgrade

---

## 7. Report Generation

### 7.1 End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INITIATES REPORT                        │
│                                                                  │
│  1. User configures report:                                     │
│     • Date range (e.g., last 30 days)                           │
│     • Platforms to include (Meta, Google, etc.)                  │
│     • Tone: executive | detailed | casual                       │
│     • AI model: Sonnet (standard) | Opus (premium)              │
│     • Template: monthly_performance                             │
│                                                                  │
│  2. POST /v1/reports/generate                                    │
│     → Create Report record (status = "processing")              │
│     → Enqueue Celery task                                        │
│     → Return 202 Accepted + report_id                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     PIPELINE EXECUTION                           │
│                     (Celery Worker)                               │
│                                                                  │
│  3. Load metric records from PostgreSQL                          │
│     (filtered by organization_id + date range + platforms)       │
│                                                                  │
│  4. PipelineOrchestrator.execute()                               │
│     ├─ Stage 1: Validate records                                │
│     ├─ Stage 2: Compute KPIs + period comparison                │
│     ├─ Stage 3+4: Trends + Anomalies (parallel)                │
│     ├─ Stage 5: Tier-classify campaigns                         │
│     ├─ Stage 6: AI insights via Claude API                      │
│     ├─ Stage 7: AI recommendations via Claude API               │
│     └─ Stage 8: Assemble PipelineResult                         │
│                                                                  │
│  5. Progress published to Redis at each stage                    │
│     (client polls GET /v1/reports/{id}/progress)                 │
│                                                                  │
│  6. Save to database:                                            │
│     • Insights → insights table                                  │
│     • Recommendations → recommendations table                   │
│     • Report metadata + executive summary → reports table        │
│                                                                  │
│  7. Publish ReportCompleted event                                │
│     → Send notification to user                                  │
│     → Invalidate dashboard cache                                 │
│     → Record AI cost for billing                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     REPORT DELIVERY                              │
│                                                                  │
│  8. User views report in browser:                                │
│     GET /v1/reports/{id}                                         │
│     → Executive summary                                         │
│     → KPI dashboard with period comparison                       │
│     → Top insights (prioritized, categorized)                    │
│     → Campaign tier breakdown                                    │
│     → Recommendations with action items                          │
│     → Trend charts + anomaly highlights                          │
│                                                                  │
│  9. Export options:                                               │
│     → Download PDF (generated + stored on S3)                    │
│     → Share client portal link (read-only, branded)              │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Report Contents

A completed report contains:

| Section | Source |
|---------|--------|
| **Executive Summary** | AI-generated (Stage 6) — 2–3 paragraphs |
| **KPI Overview** | Stage 2 — headline metrics with period comparison |
| **Campaign Performance** | Stage 5 — tier classification with efficiency scores |
| **Trends** | Stage 3 — metric direction, pacing, moving averages |
| **Anomalies** | Stage 4 — spikes, drops, correlation breaks |
| **Insights** | Stage 6 — top 3+ categorized findings |
| **Recommendations** | Stage 7 — top 3+ prioritized actions with effort/impact |
| **Platform Breakdown** | Stage 2 — per-platform spend, performance, comparison |

### 7.3 Scheduled Reports

Celery Beat triggers weekly batch generation (Monday 6 AM UTC) for organizations with scheduled reports enabled. Each report uses the same pipeline as on-demand generation.

---

## 8. Dashboard Delivery

### 8.1 Frontend Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Next.js 14 (App Router)                        │
│                                                                  │
│  Route Groups:                                                   │
│  ┌─────────┐   ┌──────────────┐   ┌──────────────────────────┐  │
│  │ (auth)  │   │ (onboarding) │   │     (dashboard)          │  │
│  │ login   │   │ wizard       │   │ dashboard · campaigns    │  │
│  │ register│   │              │   │ insights · reports       │  │
│  └─────────┘   └──────────────┘   │ clients · integrations   │  │
│                                   │ settings                 │  │
│                                   └──────────────────────────┘  │
│                                                                  │
│  Data Flow:                                                      │
│  API → api-client.ts → useQuery hooks → *-content.tsx → UI      │
│                                                                  │
│  State:                                                          │
│  Server state: TanStack React Query (5-min stale, auto-refetch) │
│  Client state: Zustand (sidebar, auth, onboarding)               │
│  URL state: search params (filters, sort, date range)            │
│  Form state: React Hook Form + Zod validation                    │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Key Dashboard Screens

#### Dashboard (Home)

```
┌───────────────────────────────────────────────────────────┐
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│  │  Spend  │ │  ROAS   │ │ Convs   │ │  CPA    │  KPI   │
│  │ $24.5K  │ │  3.2x   │ │  1,847  │ │ $13.26  │  Cards │
│  │ +12.3%  │ │  -5.1%  │ │ +23.4%  │ │ -8.7%   │        │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
│                                                           │
│  ┌─────────────────────────────┐ ┌────────────────────┐   │
│  │  Performance Over Time      │ │  Spend by Platform │   │
│  │  (dual Y-axis line chart)   │ │  (donut chart)     │   │
│  │  Spend ━━━  Conversions ━━━ │ │  Meta 45%          │   │
│  └─────────────────────────────┘ │  Google 35%        │   │
│                                  │  Shopify 20%       │   │
│  ┌─────────────────────────────┐ └────────────────────┘   │
│  │  Top Campaigns              │                          │
│  │  Name    │ Tier  │ Spend    │ ROAS  │ Score           │
│  │  Camp A  │ ★Star │ $5,200   │ 4.1x  │ ████████ 0.92  │
│  │  Camp B  │ Strong│ $3,100   │ 3.5x  │ ██████░░ 0.78  │
│  └─────────────────────────────┘                          │
└───────────────────────────────────────────────────────────┘
```

#### Insights Page
- Category filter pills (All, Performance, Efficiency, Growth, Anomaly, Risk)
- Insight cards with sentiment-colored borders (green/gray/amber)
- Recommendation cards with priority/effort badges and action checklists

#### Report Builder
- 4-step wizard: Select date range → Choose platforms → Configure tone/model → Review & generate
- Real-time pipeline progress stepper (8 stages with percentage)

#### Client Portal
- Read-only branded view for agency clients
- Shareable link with token-based access
- Executive summary + KPIs + insights (no raw data)

### 8.3 Rendering Strategy

| Pattern | Usage |
|---------|-------|
| **Server Component shell** | `page.tsx` — metadata, static layout, SEO |
| **Client Content component** | `*-content.tsx` — interactive UI with data fetching |
| **Suspense boundary** | `loading.tsx` — skeleton placeholders during data load |
| **SSR** | Client detail, report viewer (dynamic data, shareable URLs) |
| **CSR** | Onboarding wizard, report builder (heavy interactivity) |

### 8.4 Performance Targets

| Metric | Target |
|--------|--------|
| Largest Contentful Paint | < 1.5 seconds |
| First Input Delay | < 100 ms |
| Cumulative Layout Shift | < 0.1 |
| Time to Interactive | < 2.0 seconds |
| Initial JS bundle (gzipped) | < 150 KB |

---

## 9. Cross-Cutting Concerns

### 9.1 Multi-Tenancy

Every data query is scoped to `organization_id`. Isolation is enforced at three levels:

| Level | Mechanism |
|-------|-----------|
| **API** | `X-Organization-ID` header → membership verification |
| **Repository** | All queries filter by `organization_id` |
| **Database** | PostgreSQL Row-Level Security policies |

### 9.2 Security Stack

| Layer | Implementation |
|-------|---------------|
| **Authentication** | JWT (15-min access) + HttpOnly refresh cookies (7-day) |
| **Authorization** | RBAC (owner, admin, member, viewer) per organization |
| **Rate Limiting** | Sliding window — auth: 5/15min, API: 100/min, reports: 10/hr |
| **Encryption** | AES-256-GCM for OAuth tokens, TLS 1.3 in transit |
| **Security Headers** | OWASP best practices (CSP, HSTS, X-Frame-Options) |
| **Input Validation** | Pydantic (backend) + Zod (frontend) on all inputs |
| **Safe Logging** | Automatic redaction of passwords, tokens, API keys |

### 9.3 Event-Driven Architecture

Domain events decouple pipeline execution from side effects:

```
Pipeline completes → ReportCompleted event
                     ├─ Handler: Send email notification to user
                     ├─ Handler: Invalidate dashboard cache
                     └─ Handler: Record AI cost for billing

Data sync completes → DataSyncCompleted event
                      ├─ Handler: Refresh dashboard cache
                      └─ Handler: Update connection health status
```

### 9.4 Background Workers

| Queue | Tasks | Schedule |
|-------|-------|----------|
| **reports** | `generate_report`, `generate_scheduled_reports` | On-demand + weekly (Mon 6 AM) |
| **ingestion** | `sync_data_source`, `sync_all_connections` | Hourly |
| **maintenance** | `cleanup_expired_tokens`, `cleanup_stale_reports` | Daily (3 AM) |

### 9.5 Observability

| Signal | Tool |
|--------|------|
| **Structured Logs** | structlog → JSON (CloudWatch in production) |
| **Request Tracing** | X-Request-ID header propagated through all layers |
| **Pipeline Timing** | PipelineState records per-stage duration in ms |
| **AI Cost Tracking** | Token usage + cost accumulated per report |

---

## 10. Technology Stack Summary

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, React Query, Zustand, Recharts |
| **Backend API** | Python 3.12+, FastAPI, Pydantic, SQLAlchemy 2.0 (async) |
| **Database** | PostgreSQL 16 (RLS, partitioning), Redis (cache + queue broker) |
| **AI** | Claude API — Sonnet (standard), Opus (premium) |
| **Background Jobs** | Celery + Redis broker, Celery Beat for schedules |
| **Infrastructure** | AWS (ECS Fargate, RDS, ElastiCache, S3), CloudFlare CDN/WAF |
| **Auth** | JWT + bcrypt, AES-256-GCM token encryption |
| **Testing** | pytest + pytest-asyncio, httpx AsyncClient, SQLite (unit tests) |

---

## 11. Data Model (Simplified)

```
┌──────────┐     ┌───────────────┐     ┌────────────────────┐
│   User   │────►│  Membership   │◄────│   Organization     │
│          │     │  (role)       │     │  (workspace)       │
└──────────┘     └───────────────┘     └─────────┬──────────┘
                                                  │
                                    ┌─────────────┼─────────────┐
                                    │             │             │
                              ┌─────▼──────┐ ┌───▼────┐  ┌─────▼──────────┐
                              │  Campaign  │ │ Report │  │ DataSource     │
                              │            │ │        │  │ Connection     │
                              └─────┬──────┘ └───┬────┘  │ (encrypted)   │
                                    │            │       └────────────────┘
                              ┌─────▼──────┐     │
                              │  Metrics   │     ├──── Insight
                              │  (daily)   │     │
                              └────────────┘     └──── Recommendation
```

All models include UUID primary keys, `created_at`/`updated_at` timestamps, and soft-delete support.

---

## 12. Deployment Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        CloudFlare                             │
│  CDN · WAF · DDoS Protection · SSL Termination                │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                       AWS VPC                                 │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Public Subnet                                          │  │
│  │  ┌───────────────┐  ┌───────────────┐                   │  │
│  │  │ ALB           │  │ NAT Gateway   │                   │  │
│  │  │ (Load Balancer)│ │               │                   │  │
│  │  └───────┬───────┘  └───────────────┘                   │  │
│  └──────────┼──────────────────────────────────────────────┘  │
│             │                                                 │
│  ┌──────────▼──────────────────────────────────────────────┐  │
│  │  Private Subnet                                          │  │
│  │                                                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │  │
│  │  │ ECS Fargate  │  │ ECS Fargate  │  │ ECS Fargate   │  │  │
│  │  │ (API)        │  │ (Workers)    │  │ (Beat)        │  │  │
│  │  └──────┬───────┘  └──────┬───────┘  └───────────────┘  │  │
│  │         │                 │                               │  │
│  │  ┌──────▼─────────────────▼───────────────────────────┐  │  │
│  │  │                                                     │  │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │  │  │
│  │  │  │ RDS          │  │ ElastiCache  │  │ S3       │  │  │  │
│  │  │  │ PostgreSQL 16│  │ Redis        │  │ Reports  │  │  │  │
│  │  │  │ (Multi-AZ)   │  │ (Cluster)    │  │ Assets   │  │  │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────┘  │  │  │
│  │  │                                                     │  │  │
│  │  │  ┌──────────────┐                                   │  │  │
│  │  │  │ Secrets Mgr  │                                   │  │  │
│  │  │  │ (API keys)   │                                   │  │  │
│  │  │  └──────────────┘                                   │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

## 13. Key Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Clean Architecture** | API → Service → Repository → Model (no upward imports) |
| **Multi-Tenant Isolation** | `organization_id` on every query + PostgreSQL RLS |
| **Agents Orchestrate, Skills Compute** | Agents handle retry/fallback; skills are pure functions |
| **Type Safety Everywhere** | Pydantic schemas between all pipeline stages and API boundaries |
| **Fallback-First AI** | Reports always generate, even without Claude API connectivity |
| **Event-Driven Side Effects** | Domain events decouple pipeline from notifications, cache, billing |
| **Async-First** | SQLAlchemy 2.0 async, asyncio throughout, Celery for heavy work |
| **Server Components by Default** | Next.js `"use client"` only when interactivity requires it |
| **Cursor-Based Pagination** | Stable pagination at scale (no OFFSET performance issues) |
| **Defense in Depth** | Rate limiting + RBAC + RLS + encryption + validation + safe logging |
