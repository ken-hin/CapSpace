"""
MlbGameDetails — 1:1 extension of the sport-agnostic Game model.

Holds MLB-only game-level fields such as game type, starting/winning/losing
pitchers, runs by inning, and doubleheader metadata. Keyed on game_id so
cross-sport queries on the base Game table stay clean without nullable
MLB-specific columns polluting it.
"""

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.game import Game
    from app.models.player import Player


class MlbGameDetails(Base, TimestampMixin):
    """MLB-specific extension of the games table (1:1 relationship).

    Holds MLB-only game fields keyed on ``game_id`` so the cross-sport
    :class:`~app.models.game.Game` table stays free of nullable MLB columns. The
    primary key doubles as the FK back to ``games`` to enforce 1:1 cardinality.

    Attributes:
        game_id: PK and FK to the parent :class:`~app.models.game.Game`
            (cascade delete).
        mlb_game_pk: Official MLBAM gamePk; the canonical cross-system identifier.
        game_type: Game type code (``"R"`` regular, ``"P"`` postseason, ``"F"`` final,
            ``"D"`` division series, ``"L"`` league championship, ``"W"`` World Series,
            ``"S"`` spring training).
        home_starter_id: FK to the home starting pitcher (nullable for TBD).
        away_starter_id: FK to the away starting pitcher (nullable for TBD).
        winning_pitcher_id: FK to the winning pitcher (populated post-game).
        losing_pitcher_id: FK to the losing pitcher (populated post-game).
        save_pitcher_id: FK to the pitcher credited with the save (nullable).
        total_innings: Innings played (9 by default; more for extra innings).
        home_runs_by_inning: JSON array of home runs scored per inning.
        away_runs_by_inning: JSON array of away runs scored per inning.
        is_doubleheader: True if this game is part of a doubleheader.
        doubleheader_game_num: Which game of the doubleheader (1 or 2; nullable).
        game: The parent :class:`~app.models.game.Game`; the 1:1 back-reference
            paired with ``Game.mlb_details`` via ``back_populates``.
        home_starter: Eager-loaded home starting :class:`~app.models.player.Player`.
        away_starter: Eager-loaded away starting :class:`~app.models.player.Player`.
        winning_pitcher: Eager-loaded winning :class:`~app.models.player.Player`.
        losing_pitcher: Eager-loaded losing :class:`~app.models.player.Player`.
        save_pitcher: Eager-loaded save :class:`~app.models.player.Player`.
        created_at: Row creation timestamp (from :class:`TimestampMixin`).
        updated_at: Last update timestamp (from :class:`TimestampMixin`).
    """

    __tablename__ = "mlb_game_details"

    # Primary key is also the FK back to games — enforces 1:1 cardinality
    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Official MLBAM gamePk — the canonical identifier across MLB systems
    mlb_game_pk: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)

    # Game type code:
    # 'R' = Regular, 'P' = Postseason, 'F' = Final, 'D' = Division Series,
    # 'L' = League Championship, 'W' = World Series, 'S' = Spring Training
    game_type: Mapped[str] = mapped_column(String(5), nullable=False, default="R")

    # Starting pitchers (nullable for TBD / postponed games)
    home_starter_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    away_starter_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))

    # Decision pitchers (populated post-game)
    winning_pitcher_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    losing_pitcher_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    save_pitcher_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))

    # Extra-inning games (standard is 9)
    total_innings: Mapped[int | None] = mapped_column(Integer)

    # Linescore: runs scored per inning stored as JSON arrays
    # e.g. [0, 1, 0, 3, 0, 0, 2, 0, 1] for a 9-inning game
    home_runs_by_inning: Mapped[list | None] = mapped_column(JSON)
    away_runs_by_inning: Mapped[list | None] = mapped_column(JSON)

    # Doubleheader metadata
    is_doubleheader: Mapped[bool] = mapped_column(Boolean, default=False)
    doubleheader_game_num: Mapped[int | None] = mapped_column(Integer)  # 1 or 2

    # --- Relationships ---
    # Parent game (1:1). back_populates pairs with Game.mlb_details; game_id being
    # both PK and FK is what enforces the one-to-one at the DB level.
    game: Mapped["Game"] = relationship("Game", back_populates="mlb_details", lazy="selectin")
    home_starter: Mapped["Player | None"] = relationship("Player", foreign_keys=[home_starter_id], lazy="selectin")
    away_starter: Mapped["Player | None"] = relationship("Player", foreign_keys=[away_starter_id], lazy="selectin")
    winning_pitcher: Mapped["Player | None"] = relationship("Player", foreign_keys=[winning_pitcher_id], lazy="selectin")
    losing_pitcher: Mapped["Player | None"] = relationship("Player", foreign_keys=[losing_pitcher_id], lazy="selectin")
    save_pitcher: Mapped["Player | None"] = relationship("Player", foreign_keys=[save_pitcher_id], lazy="selectin")

    def __repr__(self) -> str:
        """Return a concise debug representation for logging/debugging."""
        return f"<MlbGameDetails game_id={self.game_id} pk={self.mlb_game_pk} type={self.game_type}>"
