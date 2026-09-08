from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.modules.identity.dependencies import CurrentUser

router = APIRouter(prefix="/api/workspaces/{workspace_id}/retrieval", tags=["retrieval"])


class QueryInput(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=10)


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


class RetrievalResult(BaseModel):
    trace_id: UUID
    duration_ms: float
    status: str
    results: list[RetrievedPassage]


@router.post("", response_model=RetrievalResult)
def search(workspace_id: UUID, payload: QueryInput, user: CurrentUser, request: Request):
    from app.modules.knowledge.retrieval import retrieve

    try:
        return retrieve(request.app.state.engine, workspace_id, user.id, payload.query, payload.limit)
    except ValueError as error:
        raise HTTPException(422, "Query cannot be embedded; shorten it and retry") from error
    except OSError as error:
        raise HTTPException(503, "Local embedding model is unavailable") from error
