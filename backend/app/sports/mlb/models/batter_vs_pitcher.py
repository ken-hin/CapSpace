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
    """Career head-to-head stats between a batter and pitcher.

    One row per unique (batter, pitcher) pair holding cumulative career matchup
    totals, refreshed after each game the two face each other. Useful as a feature
    input once the sample is large enough (~20+ PA). The unique constraint enforces
    one row per (batter, pitcher).

    Attributes:
        id: Surrogate primary key.
        batter_id: FK to the batting :class:`~app.models.player.Player`.
        pitcher_id: FK to the pitching :class:`~app.models.player.Player`.
        pa: Career plate appearances in this matchup.
        ab: Career at-bats in this matchup.
        hits: Career hits.
        home_runs: Career home runs.
        strikeouts: Career strikeouts.
        walks: Career walks.
        avg: Batting average (derived from counting stats; nullable).
        obp: On-base percentage (nullable).
        slg: Slugging percentage (nullable).
        xwoba: Statcast expected wOBA (requires enough batted-ball events; nullable).
        last_faced_date: Date the two most recently faced each other (nullable).
        batter: Eager-loaded batting :class:`~app.models.player.Player` relationship.
        pitcher: Eager-loaded pitching :class:`~app.models.player.Player` relationship.
        created_at: Row creation timestamp (from :class:`TimestampMixin`).
        updated_at: Last update timestamp (from :class:`TimestampMixin`).
    """

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
        """Return a concise debug representation for logging/debugging."""
        return (
            f"<BatterVsPitcher batter={self.batter_id} vs pitcher={self.pitcher_id} "
            f"pa={self.pa} avg={self.avg}>"
        )
