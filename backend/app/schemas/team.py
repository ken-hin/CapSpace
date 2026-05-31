"""Pydantic schemas for the Team resource.

Defines the request/response contract for team data: a shared base of common
fields, a create-input schema, and a response schema that serializes from the
ORM model.
"""

from pydantic import BaseModel

class TeamBase(BaseModel):
    """Fields shared by all team request/response schemas (identity and branding)."""
    name: str
    abbreviation: str
    city: str
    conference: str | None = None
    division: str | None = None
    logo_url: str | None = None

class TeamCreate(TeamBase):
    """Input schema for creating a team (no fields beyond the shared base)."""
    pass

class TeamResponse(TeamBase):
    """Output schema for a team, including its database id.

    ``from_attributes`` is enabled so instances can be built directly from the
    SQLAlchemy ORM object.
    """
    id: int
    model_config = {"from_attributes": True}
