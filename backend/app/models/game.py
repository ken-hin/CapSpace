"""Game ORM model.

Defines the sport-agnostic :class:`Game` entity: a single contest between two
teams at a venue, carrying schedule/timing, result (status and scores), season
context, and a denormalized weather snapshot captured at game time.
"""

from datetime import date, datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, Date, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
from app.models.enums import Sport


class Game(Base, TimestampMixin):
    """A single scheduled or completed game between two teams.

    Central entity that odds, predictions, feature snapshots, and stat events
    all reference. Tracks the home/away teams and venue, scheduling fields, the
    live/final result, season metadata, and a flattened set of weather columns
    describing conditions at first pitch / tip-off.

    Attributes:
        id: Surrogate primary key.
        external_id: Data provider's game identifier; unique, nullable.
        sport: Sport this game belongs to (indexed enum).
        home_team_id: FK to the home :class:`~app.models.team.Team`.
        away_team_id: FK to the away :class:`~app.models.team.Team`.
        venue_id: FK to the :class:`~app.models.venue.Venue` (nullable for TBD sites).
        scheduled_at: Scheduled first-pitch / tip-off time (tz-aware).
        game_date: Local calendar date of the game.
        start_time_actual: Actual start time once the game begins (tz-aware).
        end_time: Actual end time once the game finishes (tz-aware).
        duration_minutes: Elapsed game length in minutes.
        status: Lifecycle state, e.g. ``"scheduled"``, ``"in_progress"``, ``"final"``.
        home_score: Home team's run/point total (0 until played).
        away_score: Away team's run/point total (0 until played).
        attendance: Reported attendance, if available.
        season: Season label, e.g. ``"2026"``.
        is_postseason: True if this is a playoff/postseason game.
        weather_temp_f: Air temperature at game time, in Fahrenheit.
        weather_wind_mph: Wind speed at game time, in mph.
        weather_wind_dir_deg: Wind direction in compass degrees (0=N, 90=E).
        weather_wind_dir_text: Semantic wind direction relative to the field
            (``"in"`` | ``"out"`` | ``"L-R"`` | ``"R-L"`` | ``"cross"``).
        weather_condition: Sky/precip condition (``"clear"`` | ``"cloudy"`` |
            ``"rain"`` | ``"dome"``).
        weather_humidity_pct: Relative humidity at game time, as a percentage.
        home_team: Eager-loaded home :class:`~app.models.team.Team` relationship.
        away_team: Eager-loaded away :class:`~app.models.team.Team` relationship.
        venue: Eager-loaded :class:`~app.models.venue.Venue` relationship.
        created_at: Row creation timestamp (from :class:`TimestampMixin`).
        updated_at: Last update timestamp (from :class:`TimestampMixin`).
    """
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
        """Return a concise debug representation (id, matchup, and sport)."""
        return f"<Game {self.id}: {self.home_team_id} vs {self.away_team_id} ({self.sport})>"
