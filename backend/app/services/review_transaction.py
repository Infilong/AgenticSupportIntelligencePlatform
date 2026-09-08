"""Lock review transitions and persist their audit in the same transaction."""

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import GraphRun, GraphRunStatus
from app.models.audit import AuditLog
from app.models.review import HumanReview, ReviewDecision
from app.models.task import TaskExecution
from app.models.user import User


class HumanReviewNotFoundError(ValueError):
    pass


class HumanReviewAlreadyResolvedError(ValueError):
    pass


class HumanReviewInvalidDecisionError(ValueError):
    pass


class HumanReviewAssignmentConflictError(ValueError):
    pass


def pending_review(db: Session, *, workspace_id: UUID, review_id: UUID,
                   reviewer: User) -> HumanReview:
    review = db.scalar(
        select(HumanReview).where(
            HumanReview.workspace_id == workspace_id, HumanReview.id == review_id,
        ).with_for_update().execution_options(populate_existing=True)
    )
    if review is None:
        raise HumanReviewNotFoundError("Human review was not found.")
    if review.reviewer_decision != ReviewDecision.pending:
        raise HumanReviewAlreadyResolvedError("Human review was already resolved.")
    if db.get(TaskExecution, review.graph_run_id) is not None:
        run = db.scalar(select(GraphRun).where(GraphRun.id == review.graph_run_id,
            GraphRun.workspace_id == workspace_id).with_for_update()
            .execution_options(populate_existing=True))
        if run is None or run.status != GraphRunStatus.needs_human_review:
            raise HumanReviewAlreadyResolvedError("Task run is no longer awaiting review.")
    if review.reviewer_id is not None and review.reviewer_id != reviewer.id:
        raise HumanReviewAssignmentConflictError("Human review is assigned to another reviewer.")
    return review


def commit_review(db: Session, *, review: HumanReview, reviewer: User, action: str) -> HumanReview:
    metadata = {"graph_run_id": str(review.graph_run_id), "reason": review.reason}
    if action == "resolved":
        metadata["decision"] = review.reviewer_decision
    db.add(AuditLog(
        workspace_id=review.workspace_id, actor_user_id=reviewer.id,
        action=f"human_review.{action}", resource_type="human_review", resource_id=str(review.id),
        metadata_json=json.dumps(metadata, ensure_ascii=False, sort_keys=True),
    ))
    try:
        db.commit()
    except Exception:
        # Transaction cleanup only: preserve the original storage error for the caller/logs.
        db.rollback()
        raise
    db.refresh(review)
    return review
