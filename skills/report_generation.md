# Skill: Report Generation

## Overview

Orchestrates the end-to-end report generation pipeline — from data query through AI generation to final document assembly. Manages the DAG of agent calls, handles parallelism, error recovery, and progress tracking.

## Skill Tier: Workflow

Top-level orchestration skill that composes all agents and lower-level skills into a complete report generation pipeline.

## Pipeline Definition

```python
class ReportPipeline:
    """
    DAG-based pipeline orchestrator for report generation.

    Pipeline stages:
    1. Data Query          → parallel
    2. Analysis            → depends on [1]
    3. Anomaly Detection   → depends on [1], parallel with [2]
    4. Segmentation        → depends on [2]
    5. Insight Generation  → depends on [2, 3, 4]
    6. Recommendation Gen  → depends on [2, 3, 4, 5]
    7. Validation          → depends on [5, 6]
    8. Visualization       → depends on [2, 3, 4], parallel with [5, 6, 7]
    9. Report Assembly     → depends on [5, 6, 7, 8]
    10. PDF Generation     → depends on [9], async background

    ┌─────────┐
    │ 1. Data │
    │  Query  │
    └────┬────┘
         │
    ┌────┴──────────────┐
    │                   │
    ▼                   ▼
    ┌─────────┐   ┌──────────┐
    │ 2. Data │   │ 3. Anomaly│
    │ Analysis│   │ Detection │
    └────┬────┘   └─────┬────┘
         │              │
         ├──────────────┤
         │              │
         ▼              │
    ┌──────────┐        │
    │ 4. Segm. │        │
    └────┬─────┘        │
         │              │
         ├──────┬───────┤
         │      │       │
         ▼      ▼       │
    ┌────────┐  │       │
    │5. Insight│ │       │
    └───┬────┘  │       │
        │       │       │
        ▼       ▼       ▼
    ┌────────┐ ┌──────────┐
    │6. Reco.│ │8. Visual.│
    └───┬────┘ └────┬─────┘
        │           │
        ▼           │
    ┌────────┐      │
    │7. Valid.│      │
    └───┬────┘      │
        │           │
        ├───────────┘
        ▼
    ┌────────┐
    │9. Assem│
    └───┬────┘
        │
        ▼
    ┌────────┐
    │10. PDF │
    └────────┘
    """

    async def execute(
        self, request: ReportRequest, progress_callback: Callable
    ) -> Report:
        # Stage 1: Data Query
        progress_callback(stage="data_query", pct=5)
        metrics_data = await self.query_metrics(request)

        # Stage 2 + 3: Analysis and Anomaly Detection (parallel)
        progress_callback(stage="analysis", pct=15)
        analysis_task = self.run_data_analysis(metrics_data, request)
        anomaly_task = self.run_anomaly_detection(metrics_data, request)
        analysis, anomalies = await asyncio.gather(analysis_task, anomaly_task)

        # Stage 4: Performance Segmentation
        progress_callback(stage="segmentation", pct=30)
        segmentation = await self.run_segmentation(analysis)

        # Stage 5 + 8: Insight Generation and Visualization (parallel)
        progress_callback(stage="insights", pct=40)
        insight_task = self.run_insight_generation(analysis, anomalies, segmentation, request)
        viz_task = self.run_visualization(analysis, anomalies, segmentation)
        insights, charts = await asyncio.gather(insight_task, viz_task)

        # Stage 6: Recommendations
        progress_callback(stage="recommendations", pct=60)
        recommendations = await self.run_recommendations(
            analysis, segmentation, anomalies, insights, request
        )

        # Stage 7: Validation
        progress_callback(stage="validation", pct=75)
        validation = await self.run_validation(
            insights, recommendations, analysis, anomalies, segmentation
        )

        # Handle validation failures
        if validation.overall_verdict == "FAIL":
            insights, recommendations = await self.handle_validation_failure(
                validation, analysis, anomalies, segmentation, request
            )

        # Stage 9: Assembly
        progress_callback(stage="assembly", pct=85)
        report = await self.assemble_report(
            insights, recommendations, analysis, charts, request
        )

        # Stage 10: PDF (background)
        progress_callback(stage="pdf", pct=95)
        asyncio.create_task(self.generate_pdf_async(report))

        progress_callback(stage="complete", pct=100)
        return report
```

## Error Recovery

```python
class PipelineErrorHandler:
    MAX_RETRIES = {
        "data_query": 2,
        "analysis": 1,
        "anomaly_detection": 1,
        "segmentation": 1,
        "insight_generation": 2,      # AI calls may fail
        "recommendation_gen": 2,
        "validation": 1,
        "visualization": 1,
        "assembly": 1,
        "pdf_generation": 3,          # Async, can retry more
    }

    async def handle_stage_failure(
        self, stage: str, error: Exception, context: dict
    ) -> Any:
        retries = self.MAX_RETRIES.get(stage, 1)
        for attempt in range(retries):
            try:
                return await self.retry_stage(stage, context)
            except Exception:
                if attempt == retries - 1:
                    return self.fallback(stage, context, error)

    def fallback(self, stage: str, context: dict, error: Exception) -> Any:
        """
        Stage-specific fallbacks:
        - insight_generation: Use template-based insights
        - recommendation_gen: Use template-based recommendations
        - visualization: Use placeholder chart images
        - pdf_generation: Mark PDF as pending, notify user
        """
        FALLBACK_MAP = {
            "insight_generation": self.template_insights,
            "recommendation_gen": self.template_recommendations,
            "visualization": self.placeholder_charts,
            "pdf_generation": self.defer_pdf,
        }
        handler = FALLBACK_MAP.get(stage)
        if handler:
            return handler(context)
        raise error  # No fallback available
```

## Progress Tracking

```python
STAGE_WEIGHTS = {
    "data_query": 10,
    "analysis": 15,
    "anomaly_detection": 5,
    "segmentation": 10,
    "insights": 20,
    "recommendations": 15,
    "validation": 5,
    "visualization": 10,
    "assembly": 5,
    "pdf": 5,
}

# WebSocket events emitted at each stage:
# { "report_id": "rpt_xyz", "stage": "insights", "pct": 40, "message": "Generating insights..." }
```

## Cost Tracking

```python
class CostTracker:
    def track(self, report_id: str, stage: str, model: str, tokens: int):
        """Track AI API costs per report for billing and optimization."""
        COSTS_PER_1K = {
            "claude-sonnet-4-6": {"input": 0.003, "output": 0.015},
            "claude-opus-4-6": {"input": 0.015, "output": 0.075},
        }
```

## Used By

| Agent | Purpose |
|-------|---------|
| Report Writer Agent | Pipeline orchestration |

## Uses

| Skill/Agent | Purpose |
|------------|---------|
| Data Analysis Agent | Stage 2 |
| Anomaly Detection Agent | Stage 3 |
| Performance Segmentation Agent | Stage 4 |
| Insight Generation Agent | Stage 5 |
| Recommendation Agent | Stage 6 |
| Validation Agent | Stage 7 |
| Visualization Agent | Stage 8 |
| All atomic skills | Supporting computations |
