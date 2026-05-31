"""Celery task definitions for the ingestion pipeline.

Declares the background tasks registered on ``celery_app``: a daily schedule
fetch, a frequent live-game poll, and a one-off historical backfill. These are
currently scaffolding stubs (``pass``) to be implemented per sport; the retry
configuration and signatures are in place so they can be wired into the beat
schedule immediately.
"""

from app.ingestion.celery_app import celery_app

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_daily_schedule(self):
    """Fetch today's game schedule from the provider.

    Bound task: retries up to 3 times (60s apart) on failure. Currently a stub.

    Args:
        self: The bound Celery task instance (used to trigger retries).

    TODO:
        Implement the sport-specific schedule fetch and persistence.
    """
    try:
        pass
    except Exception as exc:
        self.retry(exc=exc)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def poll_live_games(self):
    """Poll live game stats and publish updates to Redis.

    Bound task: retries up to 3 times (10s apart) on failure. Currently a stub.

    Args:
        self: The bound Celery task instance (used to trigger retries).

    TODO:
        Implement the sport-specific live polling and Redis fan-out.
    """
    try:
        pass
    except Exception as exc:
        self.retry(exc=exc)

@celery_app.task
def ingest_historical_data(season: str):
    """Batch-import historical data for a season.

    Args:
        season: Season identifier to backfill (e.g. ``"2025"``).

    TODO:
        Implement the sport-specific historical import.
    """
    pass
