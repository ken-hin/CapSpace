"""IngestionRun ORM model.

Defines :class:`IngestionRun`, the audit-log row written for every background
(Celery) ingestion task execution. Captures status, record counts, errors, and
freeform metadata so data-freshness issues and stuck jobs can be diagnosed.
"""

from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class IngestionRun(Base):
    """
    Audit log for every Celery ingestion task execution.

    Indispensable for debugging data freshness issues. Every MLB task writes a row
    on start (status='running') and updates it on finish. If a task crashes without
    updating, the row stays 'running' and a watchdog can alert on stale runs.

    `task_name` examples: 'mlb.fetch_daily_schedule', 'mlb.fetch_yesterday_boxscores'
    `status`: 'running' | 'success' | 'failure' | 'partial'
    `metadata`: arbitrary JSON — API response codes, date ranges fetched, game PKs, etc.
    """
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Namespaced task name, e.g. 'mlb.fetch_daily_schedule'
    task_name: Mapped[str] = mapped_column(String(200), nullable=False)
    sport: Mapped[str | None] = mapped_column(String(20), index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # 'running' | 'success' | 'failure' | 'partial'
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")

    records_inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    error_message: Mapped[str | None] = mapped_column(String(2000))

    # Freeform audit data: date range, game PKs fetched, API rate-limit headers, etc.
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )

    def __repr__(self) -> str:
        """Return a concise debug representation (task name, status, start time)."""
        return f"<IngestionRun {self.task_name} status={self.status} at={self.started_at}>"
