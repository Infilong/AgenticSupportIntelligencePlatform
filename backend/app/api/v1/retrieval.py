from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.workspace import require_workspace_permission
from app.models.retrieval import RetrievalTrace
from app.models.workspace import Workspace
from app.schemas.retrieval import (
    RetrievalResultResponse,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
    RetrievalTraceResponse,
)
from app.services.retrieval_service import RetrievalError, RetrievalService

router = APIRouter(prefix="/workspaces/{workspace_id}/retrieval", tags=["retrieval"])
DbSession = Annotated[Session, Depends(get_db)]
KnowledgeReadAccess = Annotated[Workspace, Depends(require_workspace_permission("knowledge:read"))]

KnowledgeSearchAccess = Annotated[Workspace, Depends(require_workspace_permission(
    "knowledge:read", requires_active_workspace=True))]


@router.post("/search", response_model=RetrievalSearchResponse)
def search_retrieval(
    payload: RetrievalSearchRequest,
    workspace: KnowledgeSearchAccess,
    db: DbSession,
) -> RetrievalSearchResponse:
    try:
        result = RetrievalService(db).search(
            workspace_id=workspace.id,
            query=payload.query,
            language=payload.language,
            top_k=payload.top_k,
            min_score=payload.min_score,
            document_id=payload.document_id,
        )
    except RetrievalError as exc:
        if exc.trace_id is not None:
            # This direct request owns the failure transaction; graph callers own theirs.
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "retrieval_failed", "message": str(exc),
                    "trace_id": str(exc.trace_id) if exc.trace_id else None},
        ) from exc
    return RetrievalSearchResponse(
        trace_id=result.trace_id,
        language=result.language,
        strategy=result.strategy,
        no_source=result.no_source,
        results=[RetrievalResultResponse(**item.__dict__) for item in result.results],
    )


@router.get("/traces/{trace_id}", response_model=RetrievalTraceResponse)
def get_retrieval_trace(trace_id: UUID, workspace: KnowledgeReadAccess, db: DbSession):
    trace = db.scalar(select(RetrievalTrace).where(
        RetrievalTrace.workspace_id == workspace.id, RetrievalTrace.id == trace_id))
    if trace is None:
        raise HTTPException(status_code=404, detail={"code": "retrieval_trace_not_found"})
    return trace
