"""
Report generation tasks — async pipeline execution via Celery.

These tasks run the analytics pipeline in the background,
publishing progress updates to Redis for client polling.
"""

import json
import logging
from uuid import UUID

import redis

from app.core.config import get_settings
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task(
    name="app.workers.tasks.report.generate_report",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    queue="reports",
)
def generate_report(self, report_id: str, organization_id: str, request_data: dict) -> dict:
    """
    Execute the analytics pipeline for a single report.

    Publishes progress to Redis key `report:{report_id}:progress`.
    Final result is stored in Redis key `report:{report_id}:result`.
    """
    import asyncio

    from app.pipeline.orchestrator import PipelineOrchestrator
    from app.pipeline.schemas import MetricRecord, PipelineProgress, ReportRequest

    redis_client = redis.from_url(str(settings.REDIS_URL))

    def progress_callback(progress: PipelineProgress) -> None:
        redis_client.setex(
            f"report:{report_id}:progress",
            3600,
            json.dumps(progress.model_dump(), default=str),
        )

    try:
        request = ReportRequest(**request_data)
        # In production, records are fetched from the database here
        records: list[MetricRecord] = []

        orchestrator = PipelineOrchestrator()
        result = asyncio.run(
            orchestrator.execute(request, records, progress_callback)
        )

        result_data = result.model_dump(mode="json")
        redis_client.setex(
            f"report:{report_id}:result",
            86400,
            json.dumps(result_data, default=str),
        )

        logger.info("Report %s generated successfully", report_id)
        return {"status": "completed", "report_id": report_id}

    except Exception as exc:
        logger.error("Report %s generation failed: %s", report_id, exc)
        redis_client.setex(
            f"report:{report_id}:progress",
            3600,
            json.dumps({"stage": "error", "message": str(exc)}),
        )
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.workers.tasks.report.generate_scheduled_reports",
    queue="reports",
)
def generate_scheduled_reports() -> dict:
    """
    Trigger report generation for all organizations with scheduled reports.

    Called by Celery Beat on a weekly schedule (Monday 6 AM UTC).
    """
    logger.info("Checking for scheduled reports to generate")
    # TODO: Query organizations with auto_report_enabled and enqueue generate_report
    return {"status": "checked", "triggered": 0}
