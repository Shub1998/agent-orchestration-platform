from celery import Celery
from celery.signals import worker_ready
from app.config import settings

celery_app = Celery(
    "agentflow",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.execution_tasks", "app.workers.scheduled_tasks"],
)

@worker_ready.connect
def _warmup_chroma(sender, **kwargs):
    """Download the ChromaDB embedding model at worker startup so the first
    execution isn't slow. The model is cached on disk after the first download."""
    try:
        from app.core.memory_manager import memory_manager
        memory_manager._get_collection("_warmup")
        print("[worker] ChromaDB embedding model ready")
    except Exception as e:
        print(f"[worker] ChromaDB warmup skipped: {e}")


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
        "check-approval-timeouts": {
            "task": "check_approval_timeouts",
            "schedule": 300.0,  # every 5 minutes
        },
    },
)
