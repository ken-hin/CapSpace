"""Pydantic schemas for the Player resource.

Defines the request/response contract for the ``/players`` API: a shared base of
common fields, a create-input schema, and a response schema that serializes from
the ORM model.
"""

from pydantic import BaseModel

class PlayerBase(BaseModel):
    """Fields shared by all player request/response schemas (identity and role)."""
    first_name: str
    last_name: str
    position: str | None = None
    jersey_number: int | None = None
    team_id: int | None = None
    external_id: str | None = None

class PlayerCreate(PlayerBase):
    """Input schema for creating a player (no fields beyond the shared base)."""
    pass

class PlayerResponse(PlayerBase):
    """Output schema for a player, including its database id.

    ``from_attributes`` is enabled so instances can be built directly from the
    SQLAlchemy ORM object.
    """
    id: int
    model_config = {"from_attributes": True}
