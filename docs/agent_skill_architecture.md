# InsightFlow — Agent & Skill Architecture (Final)

## 1. Architecture Overview

InsightFlow uses a **modular multi-agent pipeline** with a **three-tier skill system** to process marketing data from ingestion through AI-powered report generation. The architecture follows a DAG (Directed Acyclic Graph) execution model where agents are orchestrated in dependency order with maximum parallelism.

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                    InsightFlow AI Pipeline                          │
 │                                                                     │
 │  INGESTION LAYER          ANALYSIS LAYER          GENERATION LAYER  │
 │                                                                     │
 │  ┌────────────┐      ┌──────────────────┐     ┌─────────────────┐  │
 │  │ Data       │      │ Data Analysis    │     │ Insight         │  │
 │  │ Ingestion  │─────▶│ Agent            │────▶│ Generation      │  │
 │  │ Agent      │      └────────┬─────────┘     │ Agent           │  │
 │  └─────┬──────┘               │               └────────┬────────┘  │
 │        │                      │                         │           │
 │        ▼               ┌──────┴───────┐                 │           │
 │  ┌────────────┐        │              │                 ▼           │
 │  │ Data       │   ┌────┴─────┐  ┌─────┴──────┐  ┌─────────────┐   │
 │  │ Normal-    │   │ Anomaly  │  │ Performance│  │ Recommend-  │   │
 │  │ ization    │   │ Detection│  │ Segment-   │  │ ation       │   │
 │  │ Agent      │   │ Agent    │  │ ation Agent│  │ Agent       │   │
 │  └────────────┘   └──────────┘  └────────────┘  └──────┬──────┘   │
 │                                                         │          │
 │                   QUALITY LAYER          OUTPUT LAYER    │          │
 │                                                         ▼          │
 │                   ┌──────────────┐     ┌─────────────────┐         │
 │                   │ Validation   │────▶│ Report Writer   │         │
 │                   │ Agent        │     │ Agent           │         │
 │                   └──────────────┘     └────────┬────────┘         │
 │                                                 │                  │
 │                                          ┌──────┴──────┐           │
 │                                          │ Visualization│           │
 │                                          │ Agent        │           │
 │                                          └─────────────┘           │
 └─────────────────────────────────────────────────────────────────────┘
```

## 2. Final Agents List (9 Agents)

| # | Agent | Layer | Purpose | File |
|---|-------|-------|---------|------|
| 1 | **Data Ingestion Agent** | Ingestion | Pull raw data from platform APIs (Meta, Google, GA4, Shopify) | `agents/data_ingestion_agent.md` |
| 2 | **Data Normalization Agent** | Ingestion | Transform raw data into unified schema | `agents/data_normalization_agent.md` |
| 3 | **Data Analysis Agent** | Analysis | Statistical analysis, trends, comparisons, rankings | `agents/data_analysis_agent.md` |
| 4 | **Anomaly Detection Agent** | Analysis | Detect metric outliers, pattern breaks, correlation anomalies | `agents/anomaly_detection_agent.md` |
| 5 | **Performance Segmentation Agent** | Analysis | Classify campaigns into tiers, identify budget reallocation | `agents/performance_segmentation_agent.md` |
| 6 | **Insight Generation Agent** | Generation | AI-generated insights from structured analysis data | `agents/insight_generation_agent.md` |
| 7 | **Recommendation Agent** | Generation | Actionable optimization recommendations | `agents/recommendation_agent.md` |
| 8 | **Validation Agent** | Quality | Cross-check AI output against source data | `agents/validation_agent.md` |
| 9 | **Report Writer Agent** | Output | Assemble final report (web + PDF) | `agents/report_writer_agent.md` |
| — | **Visualization Agent** | Output | Generate charts and visual data | `agents/visualization_agent.md` |

*Note: Visualization Agent operates as a sub-component of the Report Writer Agent.*

## 3. Final Skills List (8 Skills)

### Tier 1: Atomic Skills (Reusable Primitives)

| # | Skill | Purpose | File |
|---|-------|---------|------|
| 1 | **Semantic Metric Layer** | Metric definitions, formulas, platform mappings, formatting | `skills/semantic_metric_layer.md` |
| 2 | **KPI Computation** | Derived metric calculations, aggregation, scoring | `skills/kpi_computation.md` |
| 3 | **Trend Detection** | Moving averages, trend classification, pacing, seasonality | `skills/trend_detection.md` |
| 4 | **Anomaly Detection** | Z-score, IQR, contextual, correlation break detection | `skills/anomaly_detection.md` |
| 5 | **Campaign Evaluation** | Tier classification, budget assessment, diminishing returns | `skills/campaign_evaluation.md` |
| 6 | **Data Quality Validation** | Validation at every pipeline stage (raw → normalized → AI) | `skills/data_quality_validation.md` |

### Tier 2: Composite Skills (Agent Capabilities)

| # | Skill | Purpose | File |
|---|-------|---------|------|
| 7 | **Insight Summarization** | Prompt engineering, narrative templates, output parsing | `skills/insight_summarization.md` |
| 8 | **Visualization Rendering** | Chart type selection, Recharts configs, server-side render | `skills/visualization_rendering.md` |

### Tier 3: Workflow Skills (Pipeline Orchestration)

| # | Skill | Purpose | File |
|---|-------|---------|------|
| 9 | **Report Generation** | End-to-end pipeline DAG, error recovery, progress tracking | `skills/report_generation.md` |

## 4. Agent → Skill Mapping

```
┌─────────────────────────────┬───────────────────────────────────────────────────┐
│         AGENT               │                SKILLS USED                        │
├─────────────────────────────┼───────────────────────────────────────────────────┤
│                             │  SML  KPI  TRD  ANM  CEV  DQV  INS  VIZ  RPG   │
│                             │                                                   │
│ Data Ingestion Agent        │   ·    ·    ·    ·    ·    ✓    ·    ·    ·      │
│ Data Normalization Agent    │   ✓    ✓    ·    ·    ·    ✓    ·    ·    ·      │
│ Data Analysis Agent         │   ✓    ✓    ✓    ·    ·    ·    ·    ·    ·      │
│ Anomaly Detection Agent     │   ✓    ·    ·    ✓    ·    ·    ·    ·    ·      │
│ Perf. Segmentation Agent    │   ✓    ✓    ·    ·    ✓    ·    ·    ·    ·      │
│ Insight Generation Agent    │   ✓    ·    ·    ·    ·    ·    ✓    ·    ·      │
│ Recommendation Agent        │   ·    ·    ·    ·    ✓    ·    ·    ·    ·      │
│ Validation Agent            │   ✓    ✓    ·    ·    ·    ✓    ·    ·    ·      │
│ Report Writer Agent         │   ·    ·    ·    ·    ·    ·    ✓    ✓    ✓      │
│ Visualization Agent         │   ✓    ·    ·    ·    ·    ·    ·    ✓    ·      │
├─────────────────────────────┼───────────────────────────────────────────────────┤
│ LEGEND                      │                                                   │
│ SML = Semantic Metric Layer │  DQV = Data Quality Validation                   │
│ KPI = KPI Computation       │  INS = Insight Summarization                     │
│ TRD = Trend Detection       │  VIZ = Visualization Rendering                   │
│ ANM = Anomaly Detection     │  RPG = Report Generation (pipeline)              │
│ CEV = Campaign Evaluation   │                                                   │
└─────────────────────────────┴───────────────────────────────────────────────────┘
```

## 5. Complete Pipeline Execution Flow

### Report Generation DAG

```
Stage 1 ──── Data Query (metrics from DB)
             │
             ├─── parallel ────────────────────┐
             │                                  │
Stage 2 ──── Data Analysis Agent          Stage 3 ── Anomaly Detection Agent
             │                                  │
             │                                  │
Stage 4 ──── Perf. Segmentation Agent ─────────┤
             │                                  │
             ├─── parallel ────────────────────┐│
             │                                 ││
Stage 5 ──── Insight Generation Agent    Stage 8 ── Visualization Agent
             │                                 │
             │                                 │
Stage 6 ──── Recommendation Agent              │
             │                                 │
             │                                 │
Stage 7 ──── Validation Agent                  │
             │                                 │
             ├─────────────────────────────────┘
             │
Stage 9 ──── Report Assembly (Report Writer Agent)
             │
Stage 10 ─── PDF Generation (async background)
```

### Timing Estimates

| Stage | Agent | Est. Time | Cumulative |
|-------|-------|----------|-----------|
| 1 | Data Query | 1-3s | 3s |
| 2+3 | Analysis + Anomaly (parallel) | 3-5s | 8s |
| 4 | Segmentation | 1-2s | 10s |
| 5+8 | Insights + Visualization (parallel) | 5-15s | 25s |
| 6 | Recommendations | 5-10s | 35s |
| 7 | Validation | 1-3s | 38s |
| 9 | Assembly | 2-5s | 43s |
| 10 | PDF (async) | 5-10s | — |
| **Total** | | | **< 45 seconds** |

## 6. Data Flow Diagram

```
Platform APIs (Meta, Google, GA4, Shopify)
       │
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Raw Staging   │────▶│ Unified      │────▶│ Analysis     │
│ Tables        │     │ Metrics Table│     │ Output (JSON)│
│ (raw API data)│     │ (normalized) │     │              │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                           ┌──────┴───────┐
                                           │              │
                                           ▼              ▼
                                    ┌────────────┐ ┌────────────┐
                                    │ AI Insights│ │ Charts     │
                                    │ + Recs     │ │ (JSON/PNG) │
                                    │ (Claude)   │ │            │
                                    └─────┬──────┘ └─────┬──────┘
                                          │              │
                                          ▼              │
                                    ┌────────────┐       │
                                    │ Validated  │       │
                                    │ Content    │       │
                                    └─────┬──────┘       │
                                          │              │
                                          └──────┬───────┘
                                                 │
                                                 ▼
                                          ┌────────────┐
                                          │ Final      │
                                          │ Report     │
                                          │ (Web + PDF)│
                                          └────────────┘
```

## 7. Architecture Principles

### Modularity
- Each agent has a single responsibility
- Skills are reusable across agents
- Agents communicate via typed interfaces (dataclasses/Pydantic)
- Any agent can be replaced without affecting the pipeline

### Scalability
- Pipeline stages run in parallel where dependencies allow
- Celery workers scale horizontally per agent type
- Heavy stages (AI generation) can use dedicated worker pools
- Redis caching at stage boundaries prevents recomputation

### Reliability
- Each stage has configurable retry with exponential backoff
- Template-based fallbacks for AI generation failures
- Validation Agent acts as quality gate before output
- Pipeline state is persisted for crash recovery

### Security
- All data scoped to workspace_id at every stage
- OAuth tokens decrypted only at ingestion time
- AI prompts never contain cross-tenant data
- Audit logging at every pipeline stage

### Cost Optimization
- Sonnet for standard reports (~$0.02 per report)
- Opus reserved for premium deep analysis (~$0.15)
- Caching prevents duplicate AI calls
- Token budgets enforced per section
- Cost tracking per report for margin monitoring

## 8. Migration from Previous Architecture

### What Changed
| Before (3 agents, 2 skills) | After (9 agents, 9 skills) |
|------------------------------|----------------------------|
| Monolithic Data Analysis Agent | Split into: Ingestion, Normalization, Analysis, Anomaly, Segmentation |
| Monolithic Insight Generation Agent | Split into: Insight Generation, Recommendation, Validation |
| Single Report Writer Agent | Refactored with Visualization Agent sub-component |
| `marketing_data_analysis` skill | Split into: Semantic Metric Layer, KPI Computation, Trend Detection, Anomaly Detection, Campaign Evaluation, Data Quality Validation |
| `ai_report_generation` skill | Split into: Insight Summarization, Visualization Rendering, Report Generation |

### Why
1. **Single Responsibility:** Each agent/skill does one thing well
2. **Parallelism:** Fine-grained agents enable parallel execution in the DAG
3. **Testability:** Smaller units are easier to test in isolation
4. **Maintainability:** Changes to anomaly detection don't affect normalization
5. **Scalability:** Heavy stages (AI, visualization) get dedicated workers
6. **Reliability:** Validation Agent catches AI errors before they reach users
