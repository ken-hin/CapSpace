"""
BullpenAvailability — Reliever availability context per game.

Tracks recent workload for each reliever: pitches thrown in the last 1-3
days, appearances in the last week, and whether they're on a back-to-back.
This is a key input for late-game and totals modeling — a team with an
exhausted bullpen is more likely to surrender runs in innings 6-9.

One row per (game, reliever). Updated pre-game as part of lineup/bullpen prep.
"""

from datetime import datetime

from sqlalchemy import Integer, Boolean, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class BullpenAvailability(Base):
    """Reliever workload and availability status for a specific game.

    One row per (game, reliever), refreshed during pre-game prep. Recent-workload
    signals here feed late-game and totals modeling — an exhausted bullpen is more
    likely to surrender runs in innings 6-9. The unique constraint enforces one row
    per (game, player).

    Attributes:
        id: Surrogate primary key.
        game_id: FK to the :class:`~app.models.game.Game`.
        team_id: FK to the reliever's :class:`~app.models.team.Team`.
        player_id: FK to the reliever :class:`~app.models.player.Player`.
        pitches_yesterday: Pitches thrown 1 day before the game (0 if none).
        pitches_2days_ago: Pitches thrown 2 days before the game.
        pitches_3days_ago: Pitches thrown 3 days before the game.
        appearances_last_7d: Number of appearances in the prior 7 days.
        is_back_to_back: True if the reliever pitched the previous day.
        is_available: True if the reliever is expected to be available.
        updated_at: Last refresh timestamp (server default ``now()``).
        game: Eager-loaded :class:`~app.models.game.Game` relationship.
        team: Eager-loaded :class:`~app.models.team.Team` relationship.
        player: Eager-loaded reliever :class:`~app.models.player.Player` relationship.
    """

    __tablename__ = "bullpen_availability"
    __table_args__ = (
        UniqueConstraint("game_id", "player_id", name="uq_bullpen_avail_game_player"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)

    # Recent pitch counts (0 if they didn't pitch that day)
    pitches_yesterday: Mapped[int] = mapped_column(Integer, default=0)
    pitches_2days_ago: Mapped[int] = mapped_column(Integer, default=0)
    pitches_3days_ago: Mapped[int] = mapped_column(Integer, default=0)

    # Weekly workload
    appearances_last_7d: Mapped[int] = mapped_column(Integer, default=0)

    # Flags for quick filtering
    is_back_to_back: Mapped[bool] = mapped_column(Boolean, default=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    # Last refresh timestamp
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # --- Relationships ---
    game = relationship("Game", lazy="selectin")
    team = relationship("Team", lazy="selectin")
    player = relationship("Player", lazy="selectin")

    def __repr__(self) -> str:
        """Return a concise debug representation for logging/debugging."""
        return (
            f"<BullpenAvailability game={self.game_id} player={self.player_id} "
            f"avail={self.is_available} b2b={self.is_back_to_back}>"
        )
