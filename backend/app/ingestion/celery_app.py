from celery import Celery
from celery.schedules import crontab

celery_app = Celery("sports_analytics", broker="redis://localhost:6379/1", backend="redis://localhost:6379/2")
celery_app.conf.update(
    task_serializer="json", accept_content=["json"], result_serializer="json",
    timezone="UTC", enable_utc=True, task_track_started=True, task_acks_late=True, worker_prefetch_multiplier=1,
)
celery_app.conf.beat_schedule = {
    "fetch-daily-schedule": {"task": "app.ingestion.tasks.fetch_daily_schedule", "schedule": crontab(hour=7, minute=0)},
    "poll-live-games": {"task": "app.ingestion.tasks.poll_live_games", "schedule": 30.0},
}
