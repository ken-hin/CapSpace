from pydantic import BaseModel

class TeamBase(BaseModel):
    name: str
    abbreviation: str
    city: str
    conference: str | None = None
    division: str | None = None
    logo_url: str | None = None

class TeamCreate(TeamBase):
    pass

class TeamResponse(TeamBase):
    id: int
    model_config = {"from_attributes": True}
