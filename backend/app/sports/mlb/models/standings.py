"""
MlbStandings — Daily standings snapshot per team.

MLB-specific because of the runs_scored/runs_allowed and Pythagorean
win expectancy terminology. One row per (team, date) — gives a full
time-series of how each team's record evolved through the season.

Used in modeling for recent form features (last 10 record, win streak)
and Pythagorean over/underperformance as a regression signal.
"""

from datetime import date

from sqlalchemy import Integer, Float, String, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class MlbStandings(Base, TimestampMixin):
    """MLB standings snapshot for a single team on a single date."""

    __tablename__ = "mlb_standings"
    __table_args__ = (
        UniqueConstraint("team_id", "as_of_date", name="uq_mlb_standings_team_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Win-loss record
    wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    losses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    win_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Run differential
    runs_scored: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    runs_allowed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    run_diff: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Pythagorean win expectancy (Bill James formula)
    # Indicates whether a team is over/underperforming their run differential
    pythag_win_pct: Mapped[float] = mapped_column(Float, default=0.0)

    # Position in standings
    games_back: Mapped[float] = mapped_column(Float, default=0.0)
    division_rank: Mapped[int] = mapped_column(Integer, default=1)
    league_rank: Mapped[int] = mapped_column(Integer, default=1)
    wildcard_rank: Mapped[int | None] = mapped_column(Integer)

    # Recent form
    last_10_wins: Mapped[int] = mapped_column(Integer, default=0)
    last_10_losses: Mapped[int] = mapped_column(Integer, default=0)

    # Current streak
    streak_type: Mapped[str] = mapped_column(String(1), default="W")  # 'W' | 'L'
    streak_count: Mapped[int] = mapped_column(Integer, default=0)

    # --- Relationships ---
    team = relationship("Team", lazy="selectin")

    def __repr__(self) -> str:
        """Return a concise debug representation for logging/debugging."""
        return (
            f"<MlbStandings team={self.team_id} date={self.as_of_date} "
            f"record={self.wins}-{self.losses}>"
        )
