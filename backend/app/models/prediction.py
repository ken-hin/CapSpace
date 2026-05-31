"""Prediction ORM model.

Defines :class:`Prediction`, a single model output for a game/market produced
offline by the ML pipeline: probability and distributional forecasts plus
derived value metrics (edge, expected value, recommended stake) used to decide
whether a bet clears the threshold.
"""

from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Prediction(Base):
    """A pre-game prediction generated offline by the ML pipeline.

    Links a game to the model (:class:`~app.models.model_registry.ModelRegistry`)
    that produced it and records the market/side/line being predicted, the
    probability outputs, and edge/value metrics versus the book's implied
    probability. Some legacy columns are retained for backward compatibility.
    """
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)

    # Which model produced this
    model_id: Mapped[int | None] = mapped_column(ForeignKey("model_registry.id"))

    # Market / target specification
    # e.g. 'h2h' | 'spread' | 'totals' | 'player_strikeouts' | 'nrfi'
    market: Mapped[str | None] = mapped_column(String(100))
    # e.g. 'home' | 'away' | 'over' | 'under'
    side: Mapped[str | None] = mapped_column(String(20))
    line: Mapped[float | None] = mapped_column(Float)

    # Legacy fields (kept for compatibility)
    prediction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    features_used: Mapped[dict | None] = mapped_column(JSON)

    # Probability outputs
    predicted_prob: Mapped[float | None] = mapped_column(Float)
    # JSON blob for distributional forecasts (e.g. run total distribution)
    predicted_distribution: Mapped[dict | None] = mapped_column(JSON)

    # Edge / value metrics
    book_implied_prob: Mapped[float | None] = mapped_column(Float)
    edge_pct: Mapped[float | None] = mapped_column(Float)
    expected_value: Mapped[float | None] = mapped_column(Float)
    recommended_stake_pct: Mapped[float | None] = mapped_column(Float)

    # Lifecycle
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    model = relationship("ModelRegistry", lazy="selectin")

    def __repr__(self) -> str:
        """Return a concise debug representation (prediction type and game id)."""
        return f"<Prediction {self.prediction_type} game={self.game_id}>"
