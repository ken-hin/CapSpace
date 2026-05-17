from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class ClosingLine(Base):
    """
    Last odds per (game, market, book, side) snapshot before first pitch / tipoff.

    Populated by a nightly job that pulls the final BookOdds row for each combination.
    Critical for closing-line value (CLV) calculation on settled bets.

    Unique constraint enforces exactly one row per (game, book, market, period, side).
    If the source dataset has duplicates, upsert on the constraint rather than insert.
    """
    __tablename__ = "closing_lines"
    __table_args__ = (
        UniqueConstraint(
            "game_id", "book", "market", "period", "side",
            name="uq_closing_line_game_book_market_period_side",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)

    book: Mapped[str] = mapped_column(String(50), nullable=False)
    market: Mapped[str] = mapped_column(String(100), nullable=False)
    period: Mapped[str | None] = mapped_column(String(50))
    side: Mapped[str] = mapped_column(String(20), nullable=False)

    line: Mapped[float | None] = mapped_column(Float)
    american_price: Mapped[int] = mapped_column(Integer, nullable=False)
    decimal_price: Mapped[float] = mapped_column(Float, nullable=False)
    implied_prob: Mapped[float] = mapped_column(Float, nullable=False)

    # Timestamp of the captured_at value from the source BookOdds row
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<ClosingLine {self.book} {self.market} {self.side} game={self.game_id}>"
