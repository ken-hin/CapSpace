from abc import ABC, abstractmethod
from typing import Any

class BaseTransformer(ABC):
    @abstractmethod
    def transform_game(self, raw_data: dict[str, Any]) -> dict[str, Any]: ...
    @abstractmethod
    def transform_stat_events(self, raw_data: dict[str, Any]) -> list[dict[str, Any]]: ...
