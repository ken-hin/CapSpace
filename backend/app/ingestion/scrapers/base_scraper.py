"""Scraper interface.

Defines :class:`BaseScraper`, the abstract contract every provider-specific
scraper must satisfy. Concrete subclasses implement the async fetch methods for
a particular data source while the ingestion pipeline depends only on this
interface.
"""

from abc import ABC, abstractmethod
from typing import Any

class BaseScraper(ABC):
    """Abstract base for data-provider scrapers.

    Subclasses fetch raw, un-normalized payloads from an external sports-data
    source. All methods are async to allow concurrent network I/O.
    """

    @abstractmethod
    async def fetch_schedule(self, date: str) -> list[dict[str, Any]]:
        """Fetch the schedule of games for a given date.

        Args:
            date: Target date (provider-specific string format, e.g. ``YYYY-MM-DD``).

        Returns:
            list[dict[str, Any]]: Raw game records for that date.
        """
        ...
    @abstractmethod
    async def fetch_live_stats(self, game_external_id: str) -> dict[str, Any]:
        """Fetch the current live stats for an in-progress game.

        Args:
            game_external_id: The provider's identifier for the game.

        Returns:
            dict[str, Any]: Raw live-stat payload for the game.
        """
        ...
    @abstractmethod
    async def fetch_historical_games(self, season: str) -> list[dict[str, Any]]:
        """Fetch completed games for a full season (used for backfills).

        Args:
            season: Season identifier (e.g. ``"2025"``).

        Returns:
            list[dict[str, Any]]: Raw historical game records for the season.
        """
        ...
