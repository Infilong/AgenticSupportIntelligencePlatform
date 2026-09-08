from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.identity.schemas import PublicUser

Role = Literal["viewer", "operator", "admin"]


class RoleChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Role


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    role: Role


class MemberResponse(PublicUser):
    role: Role
