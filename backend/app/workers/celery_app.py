from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "ai_resume",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_max_tasks_per_child=50,
    timezone="UTC",
    beat_schedule={
        "purge-expired-candidates": {
            "task": "purge_expired_candidates",
            "schedule": 3600.0,  # hourly
        },
    },
)
