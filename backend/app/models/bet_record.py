"""BetRecord ORM model.

Defines :class:`BetRecord`, the paper- or real-money wager placed off the back
of a :class:`~app.models.prediction.Prediction`. This table is the ground truth
for evaluating model profitability, including settlement results and captured
closing-line value (CLV).
"""

from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class BetRecord(Base):
    """
    Paper-trade or real-money bet record linked to a model prediction.

    This is the ground truth for whether the model is profitable. Every prediction
    that clears the minimum-edge threshold should generate a BetRecord (paper or real).
    Settlement is written back when the game finalizes.

    `result`: 'win' | 'loss' | 'push' | 'void'
    `captured_clv_pct`: closing-line value as a percentage — positive means you beat
    the close, which is the strongest predictor of long-run profitability.
    """
    __tablename__ = "bet_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"), nullable=False)

    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Book and market details at time of bet
    book: Mapped[str] = mapped_column(String(50), nullable=False)
    market: Mapped[str] = mapped_column(String(100), nullable=False)
    side: Mapped[str] = mapped_column(String(20), nullable=False)
    line: Mapped[float | None] = mapped_column(Float)
    taken_american_price: Mapped[int] = mapped_column(Integer, nullable=False)

    # Sizing
    stake_units: Mapped[float] = mapped_column(Float, nullable=False)
    stake_dollars: Mapped[float | None] = mapped_column(Float)

    # Settlement (written after game completion)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result: Mapped[str | None] = mapped_column(String(20))
    pnl_units: Mapped[float | None] = mapped_column(Float)
    pnl_dollars: Mapped[float | None] = mapped_column(Float)

    # Positive = beat the close; the single most important metric for model quality
    captured_clv_pct: Mapped[float | None] = mapped_column(Float)

    prediction = relationship("Prediction", lazy="selectin")

    def __repr__(self) -> str:
        """Return a concise debug representation (prediction, book, market, result)."""
        return (
            f"<BetRecord prediction={self.prediction_id} {self.book} "
            f"{self.market} result={self.result}>"
        )
