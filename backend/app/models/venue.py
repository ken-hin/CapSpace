from sqlalchemy import String, Integer, Enum, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
from app.models.enums import Sport

class Venue(Base, TimestampMixin):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    sport: Mapped[Sport] = mapped_column(
      Enum(Sport, name='sport_enum', values_callable=lambda e: [s.value for s in e]),
      nullable=False,
      index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2))
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="USA")
    capacity: Mapped[int | None] = mapped_column(Integer)
    surface: Mapped[str | None] = mapped_column(String(50))
    roof_type: Mapped[str | None] = mapped_column(String(50))
    elevation_ft: Mapped[int | None] = mapped_column(Integer)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="America/New_York")
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
      return f"<Venue {self.name} ({self.city}, {self.state})>"
