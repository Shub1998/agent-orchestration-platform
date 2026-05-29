from celery import Celery
from app.config import settings

celery_app = Celery(
    "agentflow",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.execution_tasks", "app.workers.scheduled_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,
    beat_schedule={
        "check-scheduled-workflows": {
            "task": "check_scheduled_workflows",
            "schedule": 60.0,  # every 60 seconds
        },
    },
)
