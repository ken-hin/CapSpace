from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Game(Base, TimestampMixin):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")
    home_score: Mapped[int] = mapped_column(Integer, default=0)
    away_score: Mapped[int] = mapped_column(Integer, default=0)
    season: Mapped[str | None] = mapped_column(String(20))
    is_postseason: Mapped[bool] = mapped_column(Boolean, default=False)
    home_team = relationship("Team", foreign_keys=[home_team_id], lazy="selectin")
    away_team = relationship("Team", foreign_keys=[away_team_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<Game {self.id}: {self.home_team_id} vs {self.away_team_id}>"
