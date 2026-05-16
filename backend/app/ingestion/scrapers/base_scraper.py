from abc import ABC, abstractmethod
from typing import Any

class BaseScraper(ABC):
    @abstractmethod
    async def fetch_schedule(self, date: str) -> list[dict[str, Any]]: ...
    @abstractmethod
    async def fetch_live_stats(self, game_external_id: str) -> dict[str, Any]: ...
    @abstractmethod
    async def fetch_historical_games(self, season: str) -> list[dict[str, Any]]: ...
