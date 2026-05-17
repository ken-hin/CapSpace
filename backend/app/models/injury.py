from datetime import date, datetime
from sqlalchemy import String, Integer, ForeignKey, Date, DateTime, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Injury(Base):
    """Current and historical IL / injury status entries for players."""
    __tablename__ = "injuries"
    __table_args__ = (
        # Fast lookup: "what injuries is this player currently dealing with?"
        Index("ix_injuries_player_is_current", "player_id", "is_current"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)

    # Sport-specific vocabulary stored as a plain string.
    # MLB examples: 'IL10' | 'IL15' | 'IL60' | 'DTD' | 'OUT' | 'PROBABLE' | 'ACTIVE'
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500))

    started_at: Mapped[date | None] = mapped_column(Date)
    expected_return: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    player = relationship("Player", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Injury player={self.player_id} status={self.status} current={self.is_current}>"
