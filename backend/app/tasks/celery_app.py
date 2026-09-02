"""Celery application instance — DecodeX Security Technologies."""

from celery import Celery
from backend.app.core.config import settings

celery_app = Celery(
    "decodex_dld_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["backend.app.tasks.leak_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max for 1M+ rows
)
