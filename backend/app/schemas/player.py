from pydantic import BaseModel

class PlayerBase(BaseModel):
    first_name: str
    last_name: str
    position: str | None = None
    jersey_number: int | None = None
    team_id: int | None = None
    external_id: str | None = None

class PlayerCreate(PlayerBase):
    pass

class PlayerResponse(PlayerBase):
    id: int
    model_config = {"from_attributes": True}
