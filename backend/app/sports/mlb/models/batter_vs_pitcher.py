"""
BatterVsPitcher — Career head-to-head matchup stats.

Small sample sizes in many cases, but bettors and DFS players care deeply
about historical matchup data. Also useful as a feature input when sample
sizes are large enough (20+ PA).

One row per unique (batter, pitcher) pair with cumulative career stats.
Updated after each game where the two face each other.
"""

from datetime import date

from sqlalchemy import Integer, Float, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class BatterVsPitcher(Base, TimestampMixin):
    """Career head-to-head stats between a batter and pitcher."""

    __tablename__ = "batter_vs_pitcher"
    __table_args__ = (
        UniqueConstraint("batter_id", "pitcher_id", name="uq_bvp_batter_pitcher"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batter_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    pitcher_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)

    # Counting stats
    pa: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ab: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    home_runs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    strikeouts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    walks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Rate stats (computed from counting stats)
    avg: Mapped[float | None] = mapped_column(Float)
    obp: Mapped[float | None] = mapped_column(Float)
    slg: Mapped[float | None] = mapped_column(Float)

    # Statcast expected (requires enough batted-ball events)
    xwoba: Mapped[float | None] = mapped_column(Float)

    # When this matchup last occurred
    last_faced_date: Mapped[date | None] = mapped_column(Date)

    # --- Relationships ---
    batter = relationship("Player", foreign_keys=[batter_id], lazy="selectin")
    pitcher = relationship("Player", foreign_keys=[pitcher_id], lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<BatterVsPitcher batter={self.batter_id} vs pitcher={self.pitcher_id} "
            f"pa={self.pa} avg={self.avg}>"
        )
