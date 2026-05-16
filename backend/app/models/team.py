from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Team(Base, TimestampMixin):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    abbreviation: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    conference: Mapped[str | None] = mapped_column(String(50))
    division: Mapped[str | None] = mapped_column(String(50))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    players = relationship("Player", back_populates="team", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Team {self.abbreviation} - {self.name}>"
