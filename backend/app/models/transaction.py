"""Transaction ORM model.

Defines :class:`Transaction`, a record of a player roster move (trade, call-up,
designation, signing, option, recall) including the originating and destination
teams and a freeform provider payload.
"""

from datetime import date
from sqlalchemy import String, Integer, ForeignKey, Date, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Transaction(Base):
    """A roster move: trade, call-up, DFA, signing, option, or recall.

    Links the affected :class:`~app.models.player.Player` and the
    ``from``/``to`` :class:`~app.models.team.Team` (either may be null, e.g. for
    a free-agent signing) with the date and provider-supplied details.
    """
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)

    # 'trade' | 'callup' | 'designation' | 'release' | 'sign' | 'option' | 'recall'
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)

    from_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    to_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Arbitrary provider payload — notes, conditions, contract details, etc.
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    player = relationship("Player", lazy="selectin")
    from_team = relationship("Team", foreign_keys=[from_team_id], lazy="selectin")
    to_team = relationship("Team", foreign_keys=[to_team_id], lazy="selectin")

    def __repr__(self) -> str:
        """Return a concise debug representation (type, player, date)."""
        return f"<Transaction {self.transaction_type} player={self.player_id} {self.transaction_date}>"
