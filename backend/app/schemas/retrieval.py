from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.language import SupportedLanguage


class RetrievalSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    language: SupportedLanguage | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.2, ge=0.0, le=1.0)
    document_id: UUID | None = None

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("query cannot be blank")
        return stripped


class RetrievalResultResponse(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_title: str
    version: int
    chunk_index: int
    language: SupportedLanguage
    content: str
    token_count: int
    vector_score: float | None
    lexical_score: float | None
    combined_score: float
    citation: str


class RetrievalSearchResponse(BaseModel):
    trace_id: UUID
    language: SupportedLanguage
    strategy: str
    no_source: bool
    results: list[RetrievalResultResponse]


class RetrievalTraceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    graph_run_id: UUID | None
    query: str
    language: SupportedLanguage
    strategy: str
    filters_json: str
    latency_ms: int
    no_source: bool
    outcome: str
    error_code: str | None
    created_at: datetime
