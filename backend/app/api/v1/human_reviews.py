import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member, require_workspace_permission
from app.models.agent import GraphRun, GraphStep
from app.models.review import HumanReview
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.human_review import (
    HumanReviewResolveRequest,
    HumanReviewResponse,
    HumanReviewRunContext,
)
from app.services.audit_log_service import AuditLogService
from app.services.human_review_service import (
    HumanReviewAlreadyResolvedError,
    HumanReviewAssignmentConflictError,
    HumanReviewInvalidDecisionError,
    HumanReviewNotFoundError,
    HumanReviewService,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/human-reviews", tags=["human-reviews"])
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]
ReviewResolveAccess = Annotated[
    Workspace, Depends(require_workspace_permission("reviews:resolve"))
]
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


@router.post("/{review_id}/claim", response_model=HumanReviewResponse)
def claim_human_review(
    review_id: ReviewId,
    workspace: ReviewResolveAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> HumanReviewResponse:
    try:
        review = HumanReviewService(db).claim(
            workspace_id=workspace.id, review_id=review_id, reviewer=current_user
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
    except HumanReviewAssignmentConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "human_review_assignment_conflict", "message": str(exc)},
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="human_review.claimed",
        resource_type="human_review",
        resource_id=review.id,
        metadata={"graph_run_id": str(review.graph_run_id), "reason": review.reason},
    )
    return _review_response(review, db)


@router.post("/{review_id}/release", response_model=HumanReviewResponse)
def release_human_review(
    review_id: ReviewId,
    workspace: ReviewResolveAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> HumanReviewResponse:
    try:
        review = HumanReviewService(db).release(
            workspace_id=workspace.id, review_id=review_id, reviewer=current_user
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
    except HumanReviewAssignmentConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "human_review_assignment_conflict", "message": str(exc)},
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="human_review.released",
        resource_type="human_review",
        resource_id=review.id,
        metadata={"graph_run_id": str(review.graph_run_id), "reason": review.reason},
    )
    return _review_response(review, db)


@router.post("/{review_id}/resolve", response_model=HumanReviewResponse)
def resolve_human_review(
    review_id: ReviewId,
    payload: HumanReviewResolveRequest,
    workspace: ReviewResolveAccess,
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
    except HumanReviewAssignmentConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "human_review_assignment_conflict", "message": str(exc)},
        ) from exc
    except HumanReviewInvalidDecisionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "human_review_invalid_decision", "message": str(exc)},
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="human_review.resolved",
        resource_type="human_review",
        resource_id=review.id,
        metadata={
            "decision": review.reviewer_decision,
            "graph_run_id": str(review.graph_run_id),
            "reason": review.reason,
        },
    )
    return _review_response(review, db)


def _review_response(review: HumanReview, db: Session) -> HumanReviewResponse:
    response = HumanReviewResponse.model_validate(review)
    reviewer = db.get(User, review.reviewer_id) if review.reviewer_id else None
    response = response.model_copy(
        update={
            "reviewer_display_name": reviewer.display_name if reviewer else None,
            "reviewer_email": reviewer.email if reviewer else None,
        }
    )
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
            ),
            "review_context": _review_context(review=review, run=run, db=db),
        }
    )


def _review_context(*, review: HumanReview, run: GraphRun, db: Session) -> dict:
    steps = list(
        db.scalars(
            select(GraphStep)
            .where(GraphStep.workspace_id == review.workspace_id, GraphStep.graph_run_id == run.id)
            .order_by(GraphStep.created_at.asc())
        ).all()
    )
    outputs = {step.step_name: _json_object(step.output_json) for step in steps}
    classification = outputs.get("classify_intent", {})
    retrieval = outputs.get("retrieve_evidence", {})
    draft = outputs.get("draft_response", {})
    blockers = [_blocker_context(code) for code in _review_reason_codes(review.reason)]
    citations = retrieval.get("citations") if isinstance(retrieval.get("citations"), list) else []
    proposed_answer = review.proposed_answer or draft.get("draft_answer")
    return {
        "headline": _review_headline(blockers=blockers, proposed_answer=proposed_answer),
        "recommended_action": _recommended_review_action(
            blockers=blockers, proposed_answer=proposed_answer
        ),
        "can_approve": bool(proposed_answer),
        "classification": {
            "intent": classification.get("intent"),
            "sentiment": classification.get("sentiment"),
            "product_area": classification.get("product_area"),
            "safety_risk": classification.get("safety_risk"),
            "escalation_needed": classification.get("escalation_needed"),
            "confidence": classification.get("classification_confidence"),
            "rationale": classification.get("classification_rationale"),
        },
        "evidence": {
            "retrieval_trace_id": retrieval.get("retrieval_trace_id"),
            "retrieved_chunk_count": len(retrieval.get("retrieved_chunks") or []),
            "citation_count": len(citations),
            "citations": citations[:5],
            "no_source": bool(retrieval.get("no_source")),
        },
        "blockers": blockers,
    }


def _review_reason_codes(reason: str) -> list[str]:
    return [part.strip() for part in reason.split(",") if part.strip()]


def _blocker_context(code: str) -> dict:
    labels = {
        "citation_required": "Missing citations",
        "unsupported_answer": "Unsupported answer",
        "confidence_threshold": "Low confidence",
        "prompt_injection": "Prompt injection risk",
        "privacy_complaint": "Privacy complaint",
        "high_safety_risk": "High safety risk",
        "escalation_needed": "Escalation needed",
        "model_provider_failure": "Model provider failure",
        "model_budget_failure": "Model budget limit",
    }
    actions = {
        "citation_required": "Inspect retrieved evidence before approving.",
        "unsupported_answer": (
            "Reject or write a human-safe response unless policy evidence exists."
        ),
        "confidence_threshold": "Check the trace and improve the answer before release.",
        "prompt_injection": (
            "Do not follow the injected instruction; inspect trace and reject unsafe output."
        ),
        "privacy_complaint": (
            "Escalate to the privacy/support owner and avoid unsupported promises."
        ),
        "high_safety_risk": "Escalate before sending any customer-facing answer.",
        "escalation_needed": "Assign an owner and resolve with a human-authored answer.",
        "model_provider_failure": "Check model configuration or API key before retrying.",
        "model_budget_failure": "Reduce context or adjust token budget before retrying.",
    }
    critical_codes = {
        "prompt_injection",
        "privacy_complaint",
        "high_safety_risk",
        "model_provider_failure",
    }
    severity = "critical" if code in critical_codes else "warning"
    return {
        "code": code,
        "label": labels.get(code, code.replace("_", " ").title()),
        "severity": severity,
        "action": actions.get(code, "Inspect the trace before resolving."),
    }


def _review_headline(*, blockers: list[dict], proposed_answer) -> str:
    if not blockers:
        return "Review requested by workflow routing."
    lead = blockers[0]["label"]
    if proposed_answer:
        return f"Blocked by {lead}; a draft is available for review."
    return f"Blocked by {lead}; no safe draft is available yet."


def _recommended_review_action(*, blockers: list[dict], proposed_answer) -> str:
    codes = {blocker["code"] for blocker in blockers}
    if "prompt_injection" in codes:
        return "Reject unsafe output or write a response that ignores the injection."
    if "privacy_complaint" in codes or "high_safety_risk" in codes:
        return "Escalate and send only a human-approved response."
    if not proposed_answer:
        return "Inspect the trace, then reject or write a sourced human response."
    if "citation_required" in codes or "unsupported_answer" in codes:
        return "Verify citations before approving; edit or reject if evidence is missing."
    return "Review the draft and approve or edit before release."


def _json_object(raw: str) -> dict:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}
