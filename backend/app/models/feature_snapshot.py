from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class FeatureSnapshot(Base):
    """
    Pre-computed ML feature vector for a (game, side) pair at a specific feature version.

    Written by the ML pipeline's feature_builder after each morning data refresh, and
    read by the prediction service to avoid recomputing features at serve time. The
    unique constraint ensures exactly one vector per (game, side, version) — the writer
    should upsert on conflict.

    `side` is one of: 'home' | 'away' | 'matchup'
    `feature_version` examples: 'mlb_v1' | 'mlb_v2_with_arsenal'
    """
    __tablename__ = "feature_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "game_id", "side", "feature_version",
            name="uq_feature_snapshot_game_side_version",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    sport: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # 'home' | 'away' | 'matchup'
    side: Mapped[str] = mapped_column(String(20), nullable=False)
    # Semver or descriptive tag; bump whenever the feature set changes materially
    feature_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Flat dict of feature_name → value (numeric values only for now)
    features: Mapped[dict] = mapped_column(JSON, nullable=False)

    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    game = relationship("Game", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<FeatureSnapshot game={self.game_id} side={self.side} "
            f"v={self.feature_version}>"
        )
