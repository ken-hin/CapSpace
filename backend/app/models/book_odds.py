"""BookOdds ORM model.

Defines :class:`BookOdds`, a time-series record of sportsbook odds snapshots
(one row per pull) stored in a TimescaleDB hypertable. Retains the full
line-movement history needed to compute closing-line value and detect
sharp-money moves.
"""

from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, Float, ForeignKey, DateTime, Index, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class BookOdds(Base):
    """
    Time-series odds snapshots from sportsbooks.

    One row per (game, book, market, side, captured_at) pull. Retains full line-movement
    history so closing-line value and sharp-money signals can be computed.

    TimescaleDB hypertable on `captured_at`. Uses composite PK (id, captured_at) because
    TimescaleDB requires the partitioning column in any unique index/PK.
    """
    __tablename__ = "book_odds"
    __table_args__ = (
        PrimaryKeyConstraint("id", "captured_at"),
        # Primary query pattern: what are the current odds for a game across markets?
        Index("ix_book_odds_game_market_book_captured", "game_id", "market", "book", "captured_at"),
        # Player-prop query pattern: prop line history for a player
        Index("ix_book_odds_player_market_captured", "player_id", "market", "captured_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    # Null for game lines; set for player props
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))

    sport: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # 'draftkings' | 'fanduel' | 'betmgm' | 'caesars' | 'pinnacle'
    book: Mapped[str] = mapped_column(String(50), nullable=False)

    # 'h2h' | 'spread' | 'totals' | 'h2h_h1' | 'totals_h1' |
    # 'player_strikeouts' | 'player_hits' | 'player_total_bases' |
    # 'player_hr' | 'nrfi' | 'yrfi'
    market: Mapped[str] = mapped_column(String(100), nullable=False)

    # 'full_game' | 'h1' | '1st_5_innings' | '1st_inning'
    period: Mapped[str | None] = mapped_column(String(50))

    # 'home' | 'away' | 'over' | 'under'
    side: Mapped[str] = mapped_column(String(20), nullable=False)

    # Null for moneylines
    line: Mapped[float | None] = mapped_column(Float)

    american_price: Mapped[int] = mapped_column(Integer, nullable=False)
    decimal_price: Mapped[float] = mapped_column(Float, nullable=False)
    # Vig-inclusive implied probability computed from decimal_price
    implied_prob: Mapped[float] = mapped_column(Float, nullable=False)

    # Hypertable partitioning key — always tz-aware UTC
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # e.g. 'the_odds_api'
    source: Mapped[str] = mapped_column(String(100), nullable=False)

    def __repr__(self) -> str:
        """Return a concise debug representation (book, market, side, game, time)."""
        return (
            f"<BookOdds {self.book} {self.market} {self.side} "
            f"game={self.game_id} at={self.captured_at}>"
        )
