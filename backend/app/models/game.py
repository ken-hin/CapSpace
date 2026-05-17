from datetime import date, datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, Date, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
from app.models.enums import Sport


class Game(Base, TimestampMixin):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(100), unique=True)

    sport: Mapped[Sport] = mapped_column(
        Enum(Sport, name="sport_enum", values_callable=lambda e: [s.value for s in e]),
        nullable=False,
        index=True,
    )

    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    venue_id: Mapped[int | None] = mapped_column(ForeignKey("venues.id"))

    # Schedule / timing
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    game_date: Mapped[date | None] = mapped_column(Date)
    start_time_actual: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int | None] = mapped_column(Integer)

    # Result
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")
    home_score: Mapped[int] = mapped_column(Integer, default=0)
    away_score: Mapped[int] = mapped_column(Integer, default=0)
    attendance: Mapped[int | None] = mapped_column(Integer)

    # Season
    season: Mapped[str | None] = mapped_column(String(20))
    is_postseason: Mapped[bool] = mapped_column(Boolean, default=False)

    # Weather at game time
    weather_temp_f: Mapped[int | None] = mapped_column(Integer)
    weather_wind_mph: Mapped[int | None] = mapped_column(Integer)
    weather_wind_dir_deg: Mapped[int | None] = mapped_column(Integer)
    # 'in' | 'out' | 'L-R' | 'R-L' | 'cross' — semantic direction relative to field
    weather_wind_dir_text: Mapped[str | None] = mapped_column(String(20))
    # 'clear' | 'cloudy' | 'rain' | 'dome'
    weather_condition: Mapped[str | None] = mapped_column(String(50))
    weather_humidity_pct: Mapped[int | None] = mapped_column(Integer)

    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], lazy="selectin")
    away_team = relationship("Team", foreign_keys=[away_team_id], lazy="selectin")
    venue = relationship("Venue", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Game {self.id}: {self.home_team_id} vs {self.away_team_id} ({self.sport})>"
