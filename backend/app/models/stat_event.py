from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class StatEvent(Base):
    """Time-series stat event stored in a TimescaleDB hypertable.
    After creation, run: SELECT create_hypertable('stat_events', 'occurred_at');
    """
    __tablename__ = "stat_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
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
