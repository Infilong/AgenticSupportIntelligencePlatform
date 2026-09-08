"""Keep answer publication from bypassing unresolved task action approval."""

import json
from datetime import UTC, datetime

from sqlalchemy import select

from app.models.audit import AuditLog
from app.models.review import ReviewDecision
from app.models.task_action import TaskActionProposal
from app.services.review_transaction import HumanReviewInvalidDecisionError


def validate_action_reviews(db, review, decision, reviewer):
    # pending_review already owns the run lock for task-backed reviews. Action
    # resolution also takes run before proposal, so the rows cannot change here.
    proposals = list(db.scalars(select(TaskActionProposal).where(
        TaskActionProposal.workspace_id == review.workspace_id,
        TaskActionProposal.graph_run_id == review.graph_run_id,
        TaskActionProposal.status == "pending")))
    if proposals and decision != ReviewDecision.rejected:
        raise HumanReviewInvalidDecisionError(
            "Resolve the proposed task actions before the answer.")
    reject_actions(db, proposals, reviewer.id if reviewer else None, "Answer review rejected.")


def reject_actions(db, proposals, reviewer_id, reason):
    for proposal in proposals:
        proposal.status = "rejected"
        proposal.reviewer_id = reviewer_id
        proposal.resolved_at = datetime.now(UTC)
        proposal.reason = reason
        proposal.result_json = json.dumps({"applied": False, "reason": proposal.reason})
        db.add(AuditLog(workspace_id=proposal.workspace_id, actor_user_id=reviewer_id,
            action="task_action.rejected", resource_type="task_action",
            resource_id=str(proposal.id),
            metadata_json=json.dumps({"proposal_hash": proposal.proposal_hash,
                                      "reason": proposal.reason})))
