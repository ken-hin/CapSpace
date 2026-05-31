"""Transformer interface.

Defines :class:`BaseTransformer`, the abstract contract for converting raw
scraper payloads into normalized, model-ready dictionaries. Concrete subclasses
encode the mapping for a specific provider/sport.
"""

from abc import ABC, abstractmethod
from typing import Any

class BaseTransformer(ABC):
    """Abstract base for raw-payload transformers.

    Subclasses translate a provider's raw JSON into dictionaries shaped to match
    the application's ORM models.
    """

    @abstractmethod
    def transform_game(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Normalize a raw game payload into a model-ready dict.

        Args:
            raw_data: Raw game record as returned by a scraper.

        Returns:
            dict[str, Any]: Fields aligned to the :class:`~app.models.game.Game` model.
        """
        ...
    @abstractmethod
    def transform_stat_events(self, raw_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Normalize a raw payload into a list of stat-event dicts.

        Args:
            raw_data: Raw box-score / play-by-play record from a scraper.

        Returns:
            list[dict[str, Any]]: Rows aligned to the
            :class:`~app.models.stat_event.StatEvent` model.
        """
        ...
