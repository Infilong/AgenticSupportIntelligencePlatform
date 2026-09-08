"""Publish a graph outcome only after guardrails and the review queue are durable."""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import GraphRun, GraphRunStatus, GraphStep
from app.models.review import HumanReview, ReviewDecision
from app.services.graph_action_proposals import propose_task_updates
from app.services.graph_step_ordering import step_order
from app.services.guardrails import GuardrailService, has_blocking_guardrail
from app.services.support_agent_state import SupportAgentState

logger = logging.getLogger(__name__)


def publish_graph_outcome(db: Session, run: GraphRun, state: SupportAgentState) -> GraphRun:
    try:
        if state.get("route_decision") == "clarification":
            # A clarification asks for input; it asserts no policy facts and proposes no actions.
            run.language = state.get("detected_language")
            run.status = GraphRunStatus.awaiting_clarification
            run.route_decision = "clarification"
            run.final_answer = state["final_answer"]
            run.completed_at = datetime.now(UTC)
            db.commit()
            db.refresh(run)
            return run
        route_step = db.scalar(select(GraphStep).where(
            GraphStep.workspace_id == run.workspace_id, GraphStep.graph_run_id == run.id,
            GraphStep.step_name == "route_review_or_finalize",
        ).order_by(*step_order(descending=True)).limit(1))
        decisions = GuardrailService(db).evaluate_and_store(
            workspace_id=run.workspace_id, graph_run_id=run.id,
            graph_step_id=route_step.id if route_step else None, state=state, commit=False,
        )
        run.language = state.get("detected_language")
        run.completed_at = datetime.now(UTC)
        blocked = state.get("route_decision") != "finalize" or has_blocking_guardrail(decisions)
        actions = not blocked and propose_task_updates(db, run, state)
        if blocked or actions:
            reasons = sorted(set(list(state.get("route_reasons", [])) + [
                decision.guardrail_type for decision in decisions if not decision.passed
            ]))
            if actions:
                reasons.append("task_action_approval")
            run.status = GraphRunStatus.needs_human_review
            run.route_decision = "human_review"
            run.final_answer = None
            db.add(HumanReview(
                workspace_id=run.workspace_id, graph_run_id=run.id,
                reason=", ".join(reasons) or "human_review_route",
                proposed_answer=state.get("draft_answer"), reviewer_decision=ReviewDecision.pending,
            ))
        else:
            run.status = GraphRunStatus.completed
            run.route_decision = "finalize"
            run.final_answer = state.get("final_answer")
        db.commit()
    except Exception:
        # Preserve the original publication failure; never rerun graph/model work here.
        db.rollback()
        _record_publication_failure(db, run)
        raise
    db.refresh(run)
    return run


def _record_publication_failure(db: Session, run: GraphRun) -> None:
    try:
        run.status = GraphRunStatus.failed
        run.route_decision = "publication_failed"
        run.final_answer = None
        run.completed_at = datetime.now(UTC)
        db.commit()
    except Exception as exc:
        db.rollback()
        # Storage may remain unavailable. Do not replace the original exception or log content.
        logger.error("graph_publication_failure_record_failed error_type=%s", type(exc).__name__)
