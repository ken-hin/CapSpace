from app.ingestion.celery_app import celery_app

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_daily_schedule(self):
    """Fetch today's game schedule. TODO: implement for your sport."""
    try:
        pass
    except Exception as exc:
        self.retry(exc=exc)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def poll_live_games(self):
    """Poll for live game stats and publish to Redis. TODO: implement for your sport."""
    try:
        pass
    except Exception as exc:
        self.retry(exc=exc)

@celery_app.task
def ingest_historical_data(season: str):
    """Batch import historical data. TODO: implement for your sport."""
    pass
