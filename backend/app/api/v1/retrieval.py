from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.workspace import require_workspace_member
from app.models.workspace import Workspace
from app.schemas.retrieval import (
    RetrievalResultResponse,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
)
from app.services.retrieval_service import RetrievalError, RetrievalService

router = APIRouter(prefix="/workspaces/{workspace_id}/retrieval", tags=["retrieval"])
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]


@router.post("/search", response_model=RetrievalSearchResponse)
def search_retrieval(
    payload: RetrievalSearchRequest,
    workspace: WorkspaceMemberAccess,
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "retrieval_failed", "message": str(exc)},
        ) from exc
    return RetrievalSearchResponse(
        trace_id=result.trace_id,
        language=result.language,
        strategy=result.strategy,
        no_source=result.no_source,
        results=[RetrievalResultResponse(**item.__dict__) for item in result.results],
    )
