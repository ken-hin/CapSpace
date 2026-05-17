from sqlalchemy import String, Integer, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
from app.models.enums import Sport


class Team(Base, TimestampMixin):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    sport: Mapped[Sport] = mapped_column(
      Enum(Sport, name='sport_enum', values_callable=lambda e: [s.value for s in e]),
      nullable=False,
      index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    abbreviation: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    founded_year: Mapped[int | None] = mapped_column(Integer)
    league: Mapped[str | None] = mapped_column(String(50))
    conference: Mapped[str | None] = mapped_column(String(50))
    division: Mapped[str | None] = mapped_column(String(50))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    primary_color: Mapped[str | None] = mapped_column(String(10))
    secondary_color: Mapped[str| None] = mapped_column(String(10))
    home_venue_id: Mapped[int | None] = mapped_column(ForeignKey("venues.id"))
    venue = relationship("Venue", back_populates="team", lazy="selectin")
    players = relationship("Player", back_populates="team", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Team {self.abbreviation} - {self.name}>"
