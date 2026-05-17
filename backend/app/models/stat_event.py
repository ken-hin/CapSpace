from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, JSON, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class StatEvent(Base):
    """Time-series stat event stored in a TimescaleDB hypertable.

    Uses a composite PK of (id, occurred_at) because TimescaleDB requires
    the partitioning column to be part of any unique index/PK.
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
        return f"<StatEvent {self.event_type} game={self.game_id}>"
