from sqlalchemy import String, Integer, ForeignKey, Enum, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
from app.models.enums import Sport


class Player(Base, TimestampMixin):
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
        return f"<Player {self.first_name} {self.last_name}>"
