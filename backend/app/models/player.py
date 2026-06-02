"""Player ORM model.

Defines the sport-agnostic :class:`Player` entity: an athlete with biographical
details (name, birth, physical attributes), role/position metadata, and
handedness fields (``bats`` / ``throws``) that drive split-based features. Each
player optionally belongs to a current :class:`~app.models.team.Team`.
"""

from sqlalchemy import String, Integer, ForeignKey, Enum, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
from app.models.enums import Sport


class Player(Base, TimestampMixin):
    """An individual athlete.

    Sport-agnostic record keyed externally by ``external_id``. Captures identity
    and bio data plus role attributes (position, handedness) used by downstream
    feature engineering. ``team_id`` is nullable to accommodate free agents.

    Attributes:
        id: Surrogate primary key.
        external_id: Data provider's player identifier; unique, required.
        team_id: FK to the player's current :class:`~app.models.team.Team`
            (nullable for free agents).
        team: Eager-loaded current :class:`~app.models.team.Team` relationship.
        sport: Sport this player belongs to (indexed enum).
        first_name: Given name.
        last_name: Family name.
        full_name: Display name (typically ``"first last"``).
        birth_date: Date of birth.
        birth_country: Country of birth.
        height_inches: Height in inches.
        weight_lbs: Weight in pounds.
        position: Listed fielding position, e.g. ``"SS"`` or ``"SP"``.
        primary_role: High-level role, e.g. ``"batter"`` or ``"pitcher"``.
        jersey_number: Uniform number.
        bats: Batting handedness, e.g. ``"L"``, ``"R"``, or ``"S"`` (switch).
        throws: Throwing handedness, ``"L"`` or ``"R"``.
        debut_date: MLB/professional debut date.
        is_active: True if the player is currently active.
        created_at: Row creation timestamp (from :class:`TimestampMixin`).
        updated_at: Last update timestamp (from :class:`TimestampMixin`).
    """
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    team = relationship("Team", back_populates = "players", lazy = "selectin")
    sport: Mapped[Sport] = mapped_column(
      Enum(Sport, name='sport_enum', values_callable=lambda e: [s.value for s in e]),
      nullable=False,
      index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)

    birth_date: Mapped[Date | None] = mapped_column(Date)
    birth_country: Mapped[str | None] = mapped_column(String(100))

    height_inches: Mapped[int | None] = mapped_column(Integer)
    weight_lbs: Mapped[int | None] = mapped_column(Integer)

    position: Mapped[str | None] = mapped_column(String(50))
    primary_role: Mapped[str | None] = mapped_column(String(50))
    jersey_number: Mapped[int | None] = mapped_column(Integer)

    bats: Mapped[str | None] = mapped_column(String(50))
    throws: Mapped[str | None] = mapped_column(String(50))
    debut_date: Mapped[Date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        """Return a concise debug representation (player's full name)."""
        return f"<Player {self.first_name} {self.last_name}>"
