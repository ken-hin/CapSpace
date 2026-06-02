"""StatEvent ORM model.

Defines :class:`StatEvent`, a generic, sport-agnostic time-series log of
individual scoring/stat occurrences (one row per event) stored in a TimescaleDB
hypertable. It is the raw substrate the ``/stats`` aggregation endpoints query.
"""

from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, JSON, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class StatEvent(Base):
    """Time-series stat event stored in a TimescaleDB hypertable.

    Generic, sport-agnostic log of individual scoring/stat occurrences (one row
    per event) that the ``/stats`` aggregation endpoints query. Uses a composite
    PK of (id, occurred_at) because TimescaleDB requires the partitioning column
    to be part of any unique index/PK.

    Attributes:
        id: Auto-incrementing id (part of composite PK with ``occurred_at``).
        game_id: FK to the :class:`~app.models.game.Game` the event occurred in.
        player_id: FK to the :class:`~app.models.player.Player` involved (nullable).
        team_id: FK to the :class:`~app.models.team.Team` credited with the event.
        event_type: Sport-specific event label, e.g. ``"hit"`` or ``"strikeout"``.
        value: Numeric magnitude of the event (defaults to ``1.0`` for counts).
        occurred_at: Event time and hypertable partition key (tz-aware).
        period: Period/inning the event happened in (nullable).
        details: Arbitrary JSON payload with event-specific context (nullable).
    """
    __tablename__ = "stat_events"
    __table_args__ = (
        PrimaryKeyConstraint("id", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(Integer, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Float, default=1.0)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period: Mapped[str | None] = mapped_column(String(20))
    details: Mapped[dict | None] = mapped_column(JSON)

    def __repr__(self) -> str:
        """Return a concise debug representation (event type and game id)."""
        return f"<StatEvent {self.event_type} game={self.game_id}>"
