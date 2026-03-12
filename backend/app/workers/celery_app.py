"""
Celery application factory.

Configures the Celery instance with Redis broker/backend,
task serialization, and beat schedule for periodic jobs.
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()


def create_celery_app() -> Celery:
    """Create and configure the Celery application."""
    app = Celery(
        "insightflow",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )

    app.conf.update(
        # Serialization
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",

        # Timezone
        timezone="UTC",
        enable_utc=True,

        # Task settings
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,

        # Result expiry (24 hours)
        result_expires=86400,

        # Task routing
        task_routes={
            "app.workers.tasks.report.*": {"queue": "reports"},
            "app.workers.tasks.ingestion.*": {"queue": "ingestion"},
            "app.workers.tasks.maintenance.*": {"queue": "maintenance"},
        },

        # Beat schedule for periodic tasks
        beat_schedule={
            "sync-all-connections-hourly": {
                "task": "app.workers.tasks.ingestion.sync_all_connections",
                "schedule": crontab(minute=0),  # Every hour
            },
            "cleanup-expired-tokens-daily": {
                "task": "app.workers.tasks.maintenance.cleanup_expired_tokens",
                "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM UTC
            },
            "generate-scheduled-reports": {
                "task": "app.workers.tasks.report.generate_scheduled_reports",
                "schedule": crontab(hour=6, minute=0, day_of_week="mon"),  # Weekly Monday 6 AM
            },
        },
    )

    # Auto-discover tasks in the workers.tasks package
    app.autodiscover_tasks(["app.workers.tasks"])

    return app


celery_app = create_celery_app()
