"""
GameLineup — Daily batting orders for MLB games.

One row per lineup slot. Tracks the batting order position and fielding
position for each player in a game. Starters are marked with is_starter=True;
pinch-hitters / defensive replacements added mid-game can be inserted with
is_starter=False.

Critical for pre-game modeling: lineup-level OPS, handedness matchups
against the opposing starter, and lineup protection effects.
"""

from datetime import datetime

from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime, UniqueConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class GameLineup(Base):
    """Single lineup slot for an MLB game (one row per batter per team)."""

    __tablename__ = "game_lineups"
    __table_args__ = (
        UniqueConstraint(
            "game_id", "team_id", "batting_order", "is_starter",
            name="uq_game_lineups_slot",
        ),
        Index("ix_game_lineups_game_team", "game_id", "team_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)

    # Batting order position (1–9)
    batting_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Fielding position for this game
    # 'C' | '1B' | '2B' | '3B' | 'SS' | 'LF' | 'CF' | 'RF' | 'DH' | 'P'
    position: Mapped[str] = mapped_column(String(5), nullable=False)

    # Whether this player started the game in this slot
    is_starter: Mapped[bool] = mapped_column(Boolean, default=True)

    # When the lineup was confirmed/announced
    set_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # --- Relationships ---
    game = relationship("Game", lazy="selectin")
    team = relationship("Team", lazy="selectin")
    player = relationship("Player", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<GameLineup game={self.game_id} team={self.team_id} "
            f"#{self.batting_order} player={self.player_id} pos={self.position}>"
        )
