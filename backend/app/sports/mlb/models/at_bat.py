"""
AtBat — Denormalized at-bat-level rollups.

One row per plate appearance with the final outcome, RBI, runs scored,
and pitch count. Provides a convenient mid-level granularity between
game-level stats and individual pitches — useful for at-bat outcome
modeling and sequence analysis without scanning the full PitchEvent table.
"""

from datetime import datetime

from sqlalchemy import Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AtBat(Base):
    """Single plate appearance in an MLB game."""

    __tablename__ = "at_bats"
    __table_args__ = (
        UniqueConstraint("game_id", "at_bat_num", name="uq_at_bats_game_abnum"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Game context
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    inning: Mapped[int] = mapped_column(Integer, nullable=False)
    half_inning: Mapped[str] = mapped_column(String(10), nullable=False)  # 'top' | 'bottom'
    at_bat_num: Mapped[int] = mapped_column(Integer, nullable=False)

    # Participants
    pitcher_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    batter_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)

    # Denormalized handedness for split queries
    pitcher_throws: Mapped[str | None] = mapped_column(String(1))  # 'L' | 'R'
    batter_stands: Mapped[str | None] = mapped_column(String(1))   # 'L' | 'R'

    # Final outcome of the plate appearance
    # 'single' | 'double' | 'triple' | 'home_run' | 'walk' | 'strikeout' |
    # 'field_out' | 'grounded_into_double_play' | 'sac_fly' | 'hit_by_pitch' | ...
    result: Mapped[str] = mapped_column(String(100), nullable=False)

    # Run production
    rbi: Mapped[int] = mapped_column(Integer, default=0)
    runs_scored: Mapped[int] = mapped_column(Integer, default=0)

    # Pitch count for this PA
    pitch_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # --- Relationships ---
    game = relationship("Game", lazy="selectin")
    pitcher = relationship("Player", foreign_keys=[pitcher_id], lazy="selectin")
    batter = relationship("Player", foreign_keys=[batter_id], lazy="selectin")

    def __repr__(self) -> str:
        """Return a concise debug representation for logging/debugging."""
        return (
            f"<AtBat game={self.game_id} ab={self.at_bat_num} "
            f"result={self.result}>"
        )
