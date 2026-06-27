from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.language import SupportedLanguage
from app.models.knowledge import DocumentStatus


class KnowledgeDocumentUploadRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content_type: str = Field(min_length=1, max_length=80)
    content: str = Field(min_length=1)
    language: SupportedLanguage | None = None

    @field_validator("title", "content_type", "content")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value cannot be blank")
        return stripped


class KnowledgeDocumentReindexRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content_type: str | None = Field(default=None, max_length=80)
    content: str | None = Field(default=None, min_length=1)
    language: SupportedLanguage | None = None

    @field_validator("title", "content_type", "content")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("value cannot be blank")
        return stripped


class DocumentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    knowledge_document_id: UUID
    version: int
    content_hash: str
    content_type: str
    raw_text: str
    created_at: datetime


class DocumentChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    document_version_id: UUID
    language: SupportedLanguage
    chunk_index: int
    content: str
    token_count: int
    chunk_metadata: str
    created_at: datetime


class KnowledgeDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    title: str
    language: SupportedLanguage
    status: DocumentStatus
    error_message: str | None
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class KnowledgeDocumentIndexResponse(BaseModel):
    document: KnowledgeDocumentResponse
    latest_version: DocumentVersionResponse
    chunk_count: int
    embedding_count: int


class KnowledgeDocumentDetailResponse(BaseModel):
    document: KnowledgeDocumentResponse
    latest_version: DocumentVersionResponse | None
    chunks: list[DocumentChunkResponse]
    embedding_count: int
