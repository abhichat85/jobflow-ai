from celery import Celery

from app.config import settings

celery_app = Celery(
    "jobflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "check-followups-daily": {
            "task": "app.tasks.check_pending_followups",
            "schedule": 86400.0,
        },
    },
)

celery_app.autodiscover_tasks(["app"])
