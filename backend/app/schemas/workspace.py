from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.workspace import WorkspaceRole

AssignableRole = Literal[WorkspaceRole.viewer, WorkspaceRole.operator,
                         WorkspaceRole.admin, WorkspaceRole.owner]


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be blank")
        return stripped


class WorkspaceUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be blank")
        return stripped


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_by_user_id: UUID
    created_at: datetime
    archived_at: datetime | None = None
    deleted_at: datetime | None = None


class WorkspaceMembershipResponse(BaseModel):
    workspace_id: UUID
    user_id: UUID
    role: WorkspaceRole
    permissions: list[str]
    can_manage_resources: bool
    can_manage_workspace: bool


class WorkspaceMemberResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    user_id: UUID
    email: str
    display_name: str
    role: WorkspaceRole
    permissions: list[str]
    created_at: datetime


class WorkspaceMemberAddRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role: AssignableRole = WorkspaceRole.viewer

    @field_validator("email")
    @classmethod
    def normalize_email_field(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized:
            raise ValueError("email must contain @")
        return normalized


class WorkspaceMemberRoleUpdateRequest(BaseModel):
    role: AssignableRole


class WorkspaceDeleteRequest(BaseModel):
    confirmation_name: str = Field(min_length=1, max_length=160)

    @field_validator("confirmation_name")
    @classmethod
    def strip_confirmation_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("confirmation_name cannot be blank")
        return stripped


class WorkspacePermissionMatrixEntry(BaseModel):
    role: WorkspaceRole
    permissions: list[str]


class WorkspacePermissionMatrixResponse(BaseModel):
    roles: list[WorkspacePermissionMatrixEntry]
