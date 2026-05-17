from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class WeatherSnapshot(Base):
    """
    Time-series weather readings per venue.

    Useful when building weather-sensitivity features that need granularity beyond
    the single snapshot stored on Game. Pulled from Open-Meteo at forecast + actual time.

    TimescaleDB hypertable on `captured_at`. After the migration runs, execute:
        SELECT create_hypertable('weather_snapshots', 'captured_at', if_not_exists => TRUE);
    """
    __tablename__ = "weather_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
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
        return f"<WeatherSnapshot venue={self.venue_id} at={self.captured_at} {self.condition}>"
