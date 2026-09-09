from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentSummary(BaseModel):
    id: UUID
    title: str
    withdrawn: bool
    active_version_id: UUID | None
    desired_version_id: UUID | None
    version_number: int
    job_status: str | None
    error_code: str | None


class DocumentPage(BaseModel):
    items: list[DocumentSummary]
    total: int


class VersionSummary(BaseModel):
    id: UUID
    number: int
    filename: str
    checksum: str
    indexed_at: datetime | None
    job_status: str
    error_code: str | None


class DocumentDetail(BaseModel):
    document: DocumentSummary
    versions: list[VersionSummary]


class UploadResult(BaseModel):
    document_id: UUID
    version_id: UUID
    job_id: UUID


class Withdrawal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    withdrawn: bool


class SourcePreview(BaseModel):
    version_id: UUID
    text: str
    offset: int
    total_characters: int
    checksum: str
    active: bool
    withdrawn: bool


class RetrievedPassage(BaseModel):
    chunk_id: UUID
    version_id: UUID
    document_id: UUID
    title: str
    section: str
    text: str
    start_offset: int
    end_offset: int
    checksum: str
    cosine_similarity: float
    rank_score: float
