from sqlalchemy import String, Integer, Enum, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
from app.models.enums import Sport


class Venue(Base, TimestampMixin):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    sport: Mapped[Sport] = mapped_column(
        Enum(Sport, name="sport_enum", values_callable=lambda e: [s.value for s in e]),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str | None] = mapped_column(String(10))
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="USA")
    capacity: Mapped[int | None] = mapped_column(Integer)
    # 'grass' | 'turf' | 'hybrid' | 'hardwood' | 'ice' | 'clay'
    surface: Mapped[str | None] = mapped_column(String(50))
    # 'open' | 'fixed' | 'retractable'
    roof_type: Mapped[str | None] = mapped_column(String(50))
    elevation_ft: Mapped[int | None] = mapped_column(Integer)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="America/New_York")
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Back-reference: Team.venue has back_populates="team", so this attr must be named "team"
    team = relationship("Team", back_populates="venue", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Venue {self.name} ({self.city}, {self.state})>"
