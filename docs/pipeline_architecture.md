# InsightFlow Pipeline Architecture

> **Version:** 1.1 — Post architecture review
> **Location:** `backend/app/pipeline/`

---

## 1. Overview

The InsightFlow analytics pipeline transforms raw marketing metrics into AI-powered client reports through an 8-stage DAG (Directed Acyclic Graph) with parallel execution where dependencies allow.

```
                     ┌─────────────────────┐
                     │  Pipeline Entry     │
                     │  (Celery task or    │
                     │   direct invocation) │
                     └────────┬────────────┘
                              │
                     ┌────────▼────────────┐
                     │ Stage 1: Validate    │
                     └────────┬────────────┘
                              │
                     ┌────────▼────────────┐
                     │ Stage 2: KPIs        │
                     └────────┬────────────┘
                              │
               ┌──────────────┼──────────────┐
               │              │              │
      ┌────────▼────────┐   ┌▼───────────────▼──┐
      │ Stage 3: Trends  │   │ Stage 4: Anomalies │
      └────────┬────────┘   └──────┬─────────────┘
               │                    │
               └──────────┬─────────┘
                          │
                 ┌────────▼────────────┐
                 │ Stage 5: Evaluation  │
                 └────────┬────────────┘
                          │
                 ┌────────▼────────────┐
                 │ Stage 6: Insights    │ ← Claude API
                 └────────┬────────────┘
                          │
                 ┌────────▼────────────┐
                 │ Stage 7: Recommend   │ ← Claude API
                 └────────┬────────────┘
                          │
                 ┌────────▼────────────┐
                 │ Stage 8: Assemble    │
                 └────────┬────────────┘
                          │
                 ┌────────▼────────────┐
                 │   PipelineResult     │
                 └─────────────────────┘
```

---

## 2. Folder Structure

```
pipeline/
├── orchestrator.py          # DAG execution engine
├── pipeline_context.py      # Shared execution context
├── pipeline_state.py        # Stage state machine
├── schemas.py               # Inter-stage Pydantic contracts
└── stages/
    ├── stage_validation.py  # Stage 1: Data validation
    ├── stage_kpi.py         # Stage 2: KPI computation
    ├── stage_trend.py       # Stage 3: Trend detection
    ├── stage_anomaly.py     # Stage 4: Anomaly detection
    ├── stage_evaluation.py  # Stage 5: Campaign evaluation
    ├── stage_insight.py     # Stage 6: Insight generation
    ├── stage_recommendation.py # Stage 7: Recommendations
    └── stage_report.py      # Stage 8: Report assembly
```

---

## 3. Key Components

### 3.1 PipelineContext

Immutable context carrying shared configuration through all stages:

```python
@dataclass
class PipelineContext:
    report_id: UUID
    organization_id: UUID
    date_range_start: date
    date_range_end: date
    tone: str                    # executive | detailed | casual
    ai_model: str                # claude-sonnet-4-6 | claude-opus-4-6
    anthropic_client: Any        # Injected dependency
    progress_callback: Callable  # Real-time progress updates
    total_tokens_used: int       # Accumulated across AI stages
    total_ai_cost: float
```

### 3.2 PipelineState

State machine tracking per-stage execution:

```
PENDING → RUNNING → COMPLETED
                  → FAILED
                  → SKIPPED
```

Enables:
- **Progress monitoring:** API returns which stages are done/in-progress
- **Resumability:** On retry, skip already-completed stages
- **Audit trail:** Timing and error info per stage

### 3.3 Stage Executors

Each `stage_*.py` module is a thin wrapper that:
1. Marks the stage as RUNNING in PipelineState
2. Reports progress via PipelineContext
3. Instantiates the corresponding Agent
4. Calls agent.run() with typed input
5. Marks COMPLETED or FAILED in PipelineState
6. Returns typed output

### 3.4 PipelineOrchestrator

The orchestrator coordinates stages in DAG order:

```python
class PipelineOrchestrator:
    async def execute(request, records, progress_callback) -> PipelineResult:
        # Sequential: stages 1, 2
        # Parallel: stages 3 + 4 (asyncio.gather)
        # Sequential: stages 5, 6, 7, 8
```

---

## 4. Entry Points

### 4.1 Celery Task (Production)
```python
# workers/tasks/report.py
@celery_app.task
def generate_report(report_id, organization_id, request_data):
    orchestrator = PipelineOrchestrator()
    result = asyncio.run(orchestrator.execute(...))
```

### 4.2 Direct Invocation (Testing)
```python
orchestrator = PipelineOrchestrator(anthropic_client=mock_client)
result = await orchestrator.execute(request, records)
```

---

## 5. Data Contracts

All inter-stage data flows through typed Pydantic models in `schemas.py`:

| Stage | Input | Output |
|-------|-------|--------|
| 1. Validation | `list[MetricRecord]` | `ValidationResult` |
| 2. KPI | `list[MetricRecord]` + date range | `KPIResult` |
| 3. Trends | `KPIResult.records` | `TrendAnalysis` |
| 4. Anomalies | `KPIResult.records` | `AnomalyAnalysis` |
| 5. Evaluation | `KPIResult` | `CampaignEvaluationResult` |
| 6. Insights | KPIs + Trends + Anomalies + Evaluation | `InsightGenerationResult` |
| 7. Recommendations | All above + Insights | `RecommendationResult` |
| 8. Assembly | All above | `PipelineResult` |

---

## 6. Performance Targets

| Scenario | Target |
|----------|--------|
| Stages 1-5 (no AI) | < 1 second |
| With Claude Sonnet | 10-30 seconds |
| With Claude Opus | 15-45 seconds |
| Total pipeline | < 45 seconds |
| Pipeline timeout | 5 minutes (configurable) |
| Max input records | 50,000 (configurable) |

---

## 7. Fallback Strategy

| Stage | Fallback |
|-------|----------|
| 1. Validation | Continue with valid records if error rate < 50% |
| 2-5 (computational) | No AI dependency — pure math, always succeeds |
| 6. Insights | Template-based insights from data patterns |
| 7. Recommendations | Template-based recommendations from tiers |
| 8. Assembly | Always succeeds if upstream data exists |

All agents use `BaseAgent.fallback()` for degraded-mode output when retries are exhausted.

---

## 8. Event Integration

Pipeline publishes domain events for side effects:

```python
# On success:
await event_bus.publish(ReportCompleted(report_id=..., total_tokens=...))

# On failure:
await event_bus.publish(ReportFailed(report_id=..., error=..., stage=...))
```

Subscribers can handle notifications, cache invalidation, billing updates, etc.
