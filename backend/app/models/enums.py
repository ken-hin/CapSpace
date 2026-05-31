"""Shared enumerations used across the data model.

Currently defines :class:`Sport`, the canonical set of sport codes the platform
recognizes. Stored as a string-backed enum so the underlying database column
holds human-readable values (e.g. ``"mlb"``) rather than opaque integers.
"""

import enum

class Sport(str, enum.Enum):
    """Supported sport identifiers.

    Inherits from ``str`` so members compare equal to their string value and
    serialize cleanly to JSON / SQL. Members:

    - ``MLB``: Major League Baseball
    - ``NBA``: National Basketball Association
    - ``NHL``: National Hockey League
    - ``NFL``: National Football League
    - ``ATP``: ATP men's professional tennis tour
    """
    MLB = "mlb"
    NBA = "nba"
    NHL = "nhl"
    NFL = "nfl"
    ATP = "atp"
