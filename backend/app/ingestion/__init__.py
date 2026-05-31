"""Data ingestion package.

Contains the background data pipeline: the Celery application and beat schedule
(:mod:`app.ingestion.celery_app`), the task definitions (:mod:`app.ingestion.tasks`),
and the abstract :mod:`scrapers` (fetch raw data from external providers) and
:mod:`transformers` (normalize raw payloads into model-ready dicts).
"""
