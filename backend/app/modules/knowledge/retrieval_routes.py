from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.modules.identity.dependencies import CurrentUser, Database
from app.modules.knowledge.bm25 import LexicalIndexIncomplete
from app.modules.knowledge.lexical import LexicalQueryTooLong
from app.modules.knowledge.recovery import RetrievalOwnershipLost
from app.modules.knowledge.schemas import RetrievedPassage
from app.modules.knowledge.trace_read import read_trace
from app.modules.knowledge.trace_schemas import TraceDetail
from app.providers.local_reranker import InvalidRerankResult

router = APIRouter(prefix="/api/workspaces/{workspace_id}/retrieval", tags=["retrieval"])


class QueryInput(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=10)
    strategy: Literal["vector", "bm25", "hybrid", "vector_rerank", "hybrid_rerank"] = "vector_rerank"


class RetrievalResult(BaseModel):
    trace_id: UUID
    duration_ms: float
    status: str
    results: list[RetrievedPassage]


@router.post("", response_model=RetrievalResult)
def search(workspace_id: UUID, payload: QueryInput, user: CurrentUser, request: Request):
    from app.modules.knowledge.retrieval import retrieve

    try:
        return retrieve(
            request.app.state.engine,
            workspace_id,
            user.id,
            payload.query,
            payload.limit,
            strategy=payload.strategy,
        )
    except LexicalQueryTooLong as error:
        raise HTTPException(422, "Use at most 128 distinct lexical query terms") from error
    except LexicalIndexIncomplete as error:
        raise HTTPException(
            409, "Lexical index is not ready. Complete the database migration before searching."
        ) from error
    except RetrievalOwnershipLost as error:
        raise HTTPException(503, "Search was interrupted. Please retry.") from error
    except ValueError as error:
        raise HTTPException(422, "Query cannot be embedded; shorten it and retry") from error
    except OSError as error:
        raise HTTPException(503, "Local retrieval model is unavailable") from error
    except InvalidRerankResult as error:
        raise HTTPException(503, "Search scoring failed. Please retry.") from error


@router.get("/{trace_id}", response_model=TraceDetail)
def trace_detail(workspace_id: UUID, trace_id: UUID, user: CurrentUser, db: Database):
    return read_trace(db, workspace_id, trace_id, user.id)
