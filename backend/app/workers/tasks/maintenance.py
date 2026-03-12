"""
Maintenance tasks — cleanup, health checks, and housekeeping.
"""

import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.workers.tasks.maintenance.cleanup_expired_tokens",
    queue="maintenance",
)
def cleanup_expired_tokens() -> dict:
    """
    Remove expired refresh tokens and invalidated sessions.

    Runs daily at 3 AM UTC via Celery Beat.
    """
    logger.info("Cleaning up expired tokens")
    # TODO: Delete refresh tokens where expired_at < now()
    return {"status": "completed", "deleted": 0}


@celery_app.task(
    name="app.workers.tasks.maintenance.cleanup_stale_reports",
    queue="maintenance",
)
def cleanup_stale_reports() -> dict:
    """
    Clean up report generation jobs stuck in 'processing' state.

    Marks reports as failed if they've been processing for > 30 minutes.
    """
    logger.info("Checking for stale report generation jobs")
    # TODO: Update reports stuck in processing state
    return {"status": "completed", "cleaned": 0}
