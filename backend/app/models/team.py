"""Team ORM model.

Defines the sport-agnostic :class:`Team` entity: a franchise/club identified by
an external provider id, with descriptive metadata (league, division, colors,
logo) and relationships to its home venue and roster of players.
"""

from sqlalchemy import String, Integer, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
from app.models.enums import Sport


class Team(Base, TimestampMixin):
    """A sports team / franchise.

    Sport-agnostic record keyed internally by ``id`` and externally by
    ``external_id`` (the data provider's id). Holds branding and organizational
    metadata and links to its home :class:`~app.models.venue.Venue` and its
    :class:`~app.models.player.Player` roster.

    Attributes:
        id: Surrogate primary key.
        external_id: Data provider's team identifier; unique, required.
        sport: Sport this team belongs to (indexed enum).
        name: Full team name; unique.
        abbreviation: Short team code, e.g. ``"NYY"``; unique.
        city: Home city.
        founded_year: Year the franchise was founded.
        league: League/circuit, e.g. ``"AL"`` or ``"NL"`` for MLB.
        conference: Conference name (sport-dependent; may be null).
        division: Division name, e.g. ``"AL East"``.
        logo_url: URL to the team logo image.
        primary_color: Primary brand color (hex string).
        secondary_color: Secondary brand color (hex string).
        home_venue_id: FK to the home :class:`~app.models.venue.Venue`.
        venue: Eager-loaded home :class:`~app.models.venue.Venue` relationship.
        players: Eager-loaded roster of :class:`~app.models.player.Player` rows.
        created_at: Row creation timestamp (from :class:`TimestampMixin`).
        updated_at: Last update timestamp (from :class:`TimestampMixin`).
    """
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
        """Return a concise debug representation (abbreviation and name)."""
        return f"<Team {self.abbreviation} - {self.name}>"
