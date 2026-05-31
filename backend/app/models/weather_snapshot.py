"""WeatherSnapshot ORM model.

Defines :class:`WeatherSnapshot`, a time-series of per-venue weather readings
(pulled from Open-Meteo) stored in a TimescaleDB hypertable. Provides finer
granularity than the single weather snapshot denormalized onto
:class:`~app.models.game.Game`, for building weather-sensitivity features.
"""

from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class WeatherSnapshot(Base):
    """
    Time-series weather readings per venue.

    Useful when building weather-sensitivity features that need granularity beyond
    the single snapshot stored on Game. Pulled from Open-Meteo at forecast + actual time.

    TimescaleDB hypertable on `captured_at`. Uses composite PK (id, captured_at) because
    TimescaleDB requires the partitioning column in any unique index/PK.
    """
    __tablename__ = "weather_snapshots"
    __table_args__ = (
        PrimaryKeyConstraint("id", "captured_at"),
    )

    id: Mapped[int] = mapped_column(Integer, autoincrement=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), nullable=False)

    # Hypertable partitioning key — always tz-aware UTC
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    temp_f: Mapped[int | None] = mapped_column(Integer)
    wind_mph: Mapped[int | None] = mapped_column(Integer)
    # 0 = North, 90 = East, 180 = South, 270 = West
    wind_dir_deg: Mapped[int | None] = mapped_column(Integer)
    humidity_pct: Mapped[int | None] = mapped_column(Integer)
    precip_chance_pct: Mapped[int | None] = mapped_column(Integer)
    # 'clear' | 'cloudy' | 'rain' | 'snow' | 'dome' | etc.
    condition: Mapped[str | None] = mapped_column(String(50))

    venue = relationship("Venue", lazy="selectin")

    def __repr__(self) -> str:
        """Return a concise debug representation (venue, capture time, condition)."""
        return f"<WeatherSnapshot venue={self.venue_id} at={self.captured_at} {self.condition}>"
