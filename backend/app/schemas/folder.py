from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

ResourceFolderType = Literal["knowledge_document", "dataset", "evaluation_run", "agent_config"]


class ResourceFolderCreateRequest(BaseModel):
    resource_type: ResourceFolderType
    name: str = Field(min_length=1, max_length=160)
    parent_folder_id: UUID | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be blank")
        return stripped


class ResourceFolderUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    parent_folder_id: UUID | None = None

    @field_validator("name")
    @classmethod
    def strip_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be blank")
        return stripped


class ResourceFolderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    resource_type: str
    name: str
    parent_folder_id: UUID | None
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime
