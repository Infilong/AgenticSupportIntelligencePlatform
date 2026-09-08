from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


class PublicUser(BaseModel):
    id: UUID
    email: str
    display_name: str


class SessionResponse(BaseModel):
    user: PublicUser | None
    csrf_token: str
