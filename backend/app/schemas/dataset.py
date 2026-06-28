from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.dataset import ImportSourceType, ImportStatus, LabelSource, LabelType, MessageRole


class DatasetImportRequest(BaseModel):
    dataset_name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    source_type: ImportSourceType
    content: str = Field(min_length=1)
    folder_id: UUID | None = None

    @field_validator("dataset_name")
    @classmethod
    def strip_dataset_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("dataset_name cannot be blank")
        return stripped

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class DatasetFolderUpdateRequest(BaseModel):
    folder_id: UUID | None = None


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    folder_id: UUID | None
    created_at: datetime


class DatasetListResponse(BaseModel):
    items: list[DatasetResponse]
    total: int
    limit: int | None
    offset: int
    has_next: bool


class ImportBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    dataset_id: UUID
    source_type: ImportSourceType
    status: ImportStatus
    error_message: str | None
    created_at: datetime


class DatasetImportResponse(BaseModel):
    dataset: DatasetResponse
    import_batch: ImportBatchResponse
    imported_examples: int


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: MessageRole
    language: str
    content: str
    created_at: datetime


class LabelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    label_type: LabelType
    value: str
    source: LabelSource
    created_by_user_id: UUID | None
    created_at: datetime


class ConversationExampleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    dataset_id: UUID
    import_batch_id: UUID | None
    external_id: str | None
    language: str
    status: str
    created_at: datetime
    messages: list[MessageResponse]
    labels: list[LabelResponse]


class LabelEditRequest(BaseModel):
    label_type: LabelType
    value: str = Field(min_length=1, max_length=240)

    @field_validator("value")
    @classmethod
    def strip_value(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value cannot be blank")
        return stripped
