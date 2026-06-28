from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.agent import GraphRun, GraphRunStatus, GraphStepStatus, ToolCall
from app.models.ai import AIRun, AIRunStatus
from app.models.evaluation import EvaluationResult, EvaluationRun, EvaluationRunStatus
from app.models.knowledge import DocumentStatus, KnowledgeDocument
from app.models.review import GuardrailResult, HumanReview, ReviewDecision


@dataclass(frozen=True)
class AttentionItem:
    id: str
    category: str
    severity: str
    title: str
    detail: str
    count: int
    action_label: str
    target_tab: str
    target_id: str | None = None
    created_at: datetime | None = None


@dataclass(frozen=True)
class AttentionSummary:
    workspace_id: UUID
    pending_reviews: int
    assigned_to_me_reviews: int
    items: list[AttentionItem]

    @property
    def critical_count(self) -> int:
        return sum(1 for item in self.items if item.severity == "critical")

    @property
    def warning_count(self) -> int:
        return sum(1 for item in self.items if item.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for item in self.items if item.severity == "info")


class AttentionService:
    def __init__(self, db: Session):
        self.db = db

    def summarize_workspace(self, *, workspace_id: UUID, user_id: UUID) -> AttentionSummary:
        pending_reviews = self._count(
            select(func.count(HumanReview.id)).where(
                HumanReview.workspace_id == workspace_id,
                HumanReview.reviewer_decision == ReviewDecision.pending,
            )
        )
        assigned_to_me_reviews = self._count(
            select(func.count(HumanReview.id)).where(
                HumanReview.workspace_id == workspace_id,
                HumanReview.reviewer_decision == ReviewDecision.pending,
                HumanReview.reviewer_id == user_id,
            )
        )
        items = [
            item
            for item in [
                self._pending_reviews(workspace_id=workspace_id, count=pending_reviews),
                self._assigned_reviews(count=assigned_to_me_reviews),
                self._unassigned_reviews(workspace_id=workspace_id),
                self._failed_runs(workspace_id=workspace_id),
                self._failed_ai_runs(workspace_id=workspace_id),
                self._tool_failures(workspace_id=workspace_id),
                self._guardrail_failures(workspace_id=workspace_id),
                self._failed_documents(workspace_id=workspace_id),
                self._evaluation_failures(workspace_id=workspace_id),
            ]
            if item is not None
        ]
        items.sort(
            key=lambda item: (_severity_rank(item.severity), item.created_at or datetime.min),
            reverse=True,
        )
        return AttentionSummary(
            workspace_id=workspace_id,
            pending_reviews=pending_reviews,
            assigned_to_me_reviews=assigned_to_me_reviews,
            items=items,
        )

    def _pending_reviews(self, *, workspace_id: UUID, count: int) -> AttentionItem | None:
        if count == 0:
            return None
        latest = self.db.scalar(
            select(func.max(HumanReview.created_at)).where(
                HumanReview.workspace_id == workspace_id,
                HumanReview.reviewer_decision == ReviewDecision.pending,
            )
        )
        return AttentionItem(
            id="pending_reviews",
            category="human_review",
            severity="warning",
            title="Human review queue",
            detail="Agent outputs are waiting for approval, edit, or rejection before completion.",
            count=count,
            action_label="Open review queue",
            target_tab="reviews",
            created_at=latest,
        )

    def _assigned_reviews(self, *, count: int) -> AttentionItem | None:
        if count == 0:
            return None
        return AttentionItem(
            id="assigned_reviews",
            category="human_review",
            severity="critical",
            title="Reviews assigned to me",
            detail=(
                "You own these pending review decisions. "
                "Resolve or release them to keep the workflow moving."
            ),
            count=count,
            action_label="Review my queue",
            target_tab="reviews",
        )

    def _unassigned_reviews(self, *, workspace_id: UUID) -> AttentionItem | None:
        count = self._count(
            select(func.count(HumanReview.id)).where(
                HumanReview.workspace_id == workspace_id,
                HumanReview.reviewer_decision == ReviewDecision.pending,
                HumanReview.reviewer_id.is_(None),
            )
        )
        if count == 0:
            return None
        latest = self.db.scalar(
            select(func.max(HumanReview.created_at)).where(
                HumanReview.workspace_id == workspace_id,
                HumanReview.reviewer_decision == ReviewDecision.pending,
                HumanReview.reviewer_id.is_(None),
            )
        )
        return AttentionItem(
            id="unassigned_reviews",
            category="human_review",
            severity="warning",
            title="Unassigned reviews",
            detail="Reviewer tasks are waiting to be claimed by an operator.",
            count=count,
            action_label="Claim review",
            target_tab="reviews",
            created_at=latest,
        )

    def _failed_runs(self, *, workspace_id: UUID) -> AttentionItem | None:
        count = self._count(
            select(func.count(GraphRun.id)).where(
                GraphRun.workspace_id == workspace_id,
                GraphRun.status == GraphRunStatus.failed,
            )
        )
        if count == 0:
            return None
        latest_run = self.db.scalar(
            select(GraphRun)
            .where(
                GraphRun.workspace_id == workspace_id,
                GraphRun.status == GraphRunStatus.failed,
            )
            .order_by(GraphRun.created_at.desc())
        )
        return AttentionItem(
            id="failed_graph_runs",
            category="runs",
            severity="critical",
            title="Failed graph runs",
            detail=(
                "At least one LangGraph execution failed or was rejected "
                "and needs trace inspection."
            ),
            count=count,
            action_label="Inspect trace",
            target_tab="trace",
            target_id=str(latest_run.id) if latest_run else None,
            created_at=latest_run.created_at if latest_run else None,
        )

    def _failed_ai_runs(self, *, workspace_id: UUID) -> AttentionItem | None:
        count = self._count(
            select(func.count(AIRun.id)).where(
                AIRun.workspace_id == workspace_id,
                AIRun.status == AIRunStatus.failed,
            )
        )
        if count == 0:
            return None
        latest_ai_run = self.db.scalar(
            select(AIRun)
            .where(
                AIRun.workspace_id == workspace_id,
                AIRun.status == AIRunStatus.failed,
            )
            .order_by(AIRun.created_at.desc())
        )
        has_trace = latest_ai_run is not None and latest_ai_run.graph_run_id is not None
        return AttentionItem(
            id="failed_model_calls",
            category="models",
            severity="critical",
            title="Failed model calls",
            detail="Model provider or budget failures are visible in traces and the AI run ledger.",
            count=count,
            action_label="Inspect trace" if has_trace else "Open usage ledger",
            target_tab="trace" if has_trace else "costs",
            target_id=str(latest_ai_run.graph_run_id) if has_trace else None,
            created_at=latest_ai_run.created_at if latest_ai_run else None,
        )

    def _tool_failures(self, *, workspace_id: UUID) -> AttentionItem | None:
        count = self._count(
            select(func.count(ToolCall.id)).where(
                ToolCall.workspace_id == workspace_id,
                ToolCall.status == GraphStepStatus.failed,
            )
        )
        if count == 0:
            return None
        latest_tool_call = self.db.scalar(
            select(ToolCall)
            .where(
                ToolCall.workspace_id == workspace_id,
                ToolCall.status == GraphStepStatus.failed,
            )
            .order_by(ToolCall.created_at.desc())
        )
        return AttentionItem(
            id="tool_failures",
            category="tools",
            severity="critical",
            title="Tool failures",
            detail=(
                "Agent tool calls failed and should be inspected "
                "from tool history or trace steps."
            ),
            count=count,
            action_label="Inspect trace",
            target_tab="trace",
            target_id=str(latest_tool_call.graph_run_id) if latest_tool_call else None,
            created_at=latest_tool_call.created_at if latest_tool_call else None,
        )

    def _guardrail_failures(self, *, workspace_id: UUID) -> AttentionItem | None:
        count = self._count(
            select(func.count(GuardrailResult.id)).where(
                GuardrailResult.workspace_id == workspace_id,
                GuardrailResult.passed.is_(False),
            )
        )
        if count == 0:
            return None
        latest = self.db.scalar(
            select(func.max(GuardrailResult.created_at)).where(
                GuardrailResult.workspace_id == workspace_id,
                GuardrailResult.passed.is_(False),
            )
        )
        return AttentionItem(
            id="guardrail_failures",
            category="guardrails",
            severity="warning",
            title="Guardrail blocks",
            detail=(
                "Governance checks blocked or routed outputs. "
                "Review policy result and linked trace."
            ),
            count=count,
            action_label="Open guardrails",
            target_tab="guardrails",
            created_at=latest,
        )

    def _failed_documents(self, *, workspace_id: UUID) -> AttentionItem | None:
        count = self._count(
            select(func.count(KnowledgeDocument.id)).where(
                KnowledgeDocument.workspace_id == workspace_id,
                KnowledgeDocument.status == DocumentStatus.failed,
            )
        )
        if count == 0:
            return None
        latest = self.db.scalar(
            select(func.max(KnowledgeDocument.updated_at)).where(
                KnowledgeDocument.workspace_id == workspace_id,
                KnowledgeDocument.status == DocumentStatus.failed,
            )
        )
        return AttentionItem(
            id="failed_documents",
            category="knowledge",
            severity="critical",
            title="Knowledge indexing failures",
            detail="Failed documents cannot be retrieved or cited by the agent.",
            count=count,
            action_label="Open knowledge",
            target_tab="documents",
            created_at=latest,
        )

    def _evaluation_failures(self, *, workspace_id: UUID) -> AttentionItem | None:
        failed_results = self._count(
            select(func.count(EvaluationResult.id)).where(
                EvaluationResult.workspace_id == workspace_id,
                EvaluationResult.passed.is_(False),
            )
        )
        failed_runs = self._count(
            select(func.count(EvaluationRun.id)).where(
                EvaluationRun.workspace_id == workspace_id,
                EvaluationRun.status == EvaluationRunStatus.failed,
            )
        )
        count = failed_results + failed_runs
        if count == 0:
            return None
        latest = self.db.scalar(
            select(func.max(EvaluationResult.created_at)).where(
                EvaluationResult.workspace_id == workspace_id,
                EvaluationResult.passed.is_(False),
            )
        )
        return AttentionItem(
            id="evaluation_failures",
            category="evaluations",
            severity="warning",
            title="Evaluation failures",
            detail=(
                "Quality, routing, citation, or language-preservation checks "
                "failed in evaluations."
            ),
            count=count,
            action_label="Open evaluations",
            target_tab="evaluations",
            created_at=latest,
        )

    def _count(self, statement) -> int:
        return int(self.db.scalar(statement) or 0)


def _severity_rank(severity: str) -> int:
    return {"critical": 3, "warning": 2, "info": 1}.get(severity, 0)
