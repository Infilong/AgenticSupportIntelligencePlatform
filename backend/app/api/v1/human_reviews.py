from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member
from app.models.agent import GraphRun
from app.models.review import HumanReview
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.human_review import (
    HumanReviewResolveRequest,
    HumanReviewResponse,
    HumanReviewRunContext,
)
from app.services.human_review_service import (
    HumanReviewAlreadyResolvedError,
    HumanReviewInvalidDecisionError,
    HumanReviewNotFoundError,
    HumanReviewService,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/human-reviews", tags=["human-reviews"])
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]
CurrentUser = Annotated[User, Depends(get_current_user)]
ReviewId = Annotated[UUID, Path()]


@router.get("", response_model=list[HumanReviewResponse])
def list_human_reviews(
    workspace: WorkspaceMemberAccess,
    db: DbSession,
) -> list[HumanReviewResponse]:
    reviews = HumanReviewService(db).list_reviews(workspace_id=workspace.id)
    return [_review_response(review, db) for review in reviews]


@router.get("/{review_id}", response_model=HumanReviewResponse)
def get_human_review(
    review_id: ReviewId,
    workspace: WorkspaceMemberAccess,
    db: DbSession,
) -> HumanReviewResponse:
    try:
        review = HumanReviewService(db).get_review(workspace_id=workspace.id, review_id=review_id)
    except HumanReviewNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "human_review_not_found", "message": "Human review was not found."},
        ) from exc
    return _review_response(review, db)


@router.post("/{review_id}/resolve", response_model=HumanReviewResponse)
def resolve_human_review(
    review_id: ReviewId,
    payload: HumanReviewResolveRequest,
    workspace: WorkspaceMemberAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> HumanReviewResponse:
    try:
        review = HumanReviewService(db).resolve(
            workspace_id=workspace.id,
            review_id=review_id,
            reviewer=current_user,
            decision=payload.decision,
            edited_answer=payload.edited_answer,
            comments=payload.comments,
        )
    except HumanReviewNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "human_review_not_found", "message": "Human review was not found."},
        ) from exc
    except HumanReviewAlreadyResolvedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "human_review_already_resolved", "message": str(exc)},
        ) from exc
    except HumanReviewInvalidDecisionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "human_review_invalid_decision", "message": str(exc)},
        ) from exc
    return _review_response(review, db)


def _review_response(review: HumanReview, db: Session) -> HumanReviewResponse:
    response = HumanReviewResponse.model_validate(review)
    run = db.scalar(
        select(GraphRun).where(
            GraphRun.workspace_id == review.workspace_id,
            GraphRun.id == review.graph_run_id,
        )
    )
    if run is None:
        return response
    return response.model_copy(
        update={
            "run": HumanReviewRunContext(
                graph_run_id=run.id,
                input_message=run.input_message,
                language=run.language,
                status=run.status,
                route_decision=run.route_decision,
                final_answer=run.final_answer,
                created_at=run.created_at,
                completed_at=run.completed_at,
            )
        }
    )
