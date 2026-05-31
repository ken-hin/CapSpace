"""Celery application and beat schedule for background ingestion.

Configures the shared ``celery_app`` (Redis broker + result backend, JSON
serialization, UTC scheduling) and the periodic ``beat_schedule`` that drives
recurring ingestion: a daily schedule pull and a frequent live-game poll. The
worker and beat processes both import ``celery_app`` from this module.
"""

from celery import Celery
from celery.schedules import crontab

# Celery app: broker on Redis DB 1, results on Redis DB 2.
celery_app = Celery("sports_analytics", broker="redis://localhost:6379/1", backend="redis://localhost:6379/2")
celery_app.conf.update(
    # JSON-only (de)serialization, UTC scheduling, and at-most-one-task-per-worker
    # prefetch so long-running ingestion tasks don't starve each other.
    task_serializer="json", accept_content=["json"], result_serializer="json",
    timezone="UTC", enable_utc=True, task_track_started=True, task_acks_late=True, worker_prefetch_multiplier=1,
)
# Periodic schedule consumed by `celery beat`: daily schedule fetch at 07:00 UTC,
# and a live-game poll every 30 seconds.
celery_app.conf.beat_schedule = {
    "fetch-daily-schedule": {"task": "app.ingestion.tasks.fetch_daily_schedule", "schedule": crontab(hour=7, minute=0)},
    "poll-live-games": {"task": "app.ingestion.tasks.poll_live_games", "schedule": 30.0},
}
