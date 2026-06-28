from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.review import GuardrailResult


@dataclass(frozen=True)
class GuardrailDefinition:
    guardrail_type: str
    label: str
    description: str
    stage: str
    enabled: bool
    configurable: bool
    default_severity: str
    action_on_fail: str
    related_workflow_nodes: list[str]


@dataclass(frozen=True)
class GuardrailUsageSummary:
    total_evaluations: int
    failed_evaluations: int
    pass_rate: float
    last_failed_at: datetime | None


@dataclass(frozen=True)
class GuardrailFailure:
    id: UUID
    graph_run_id: UUID
    graph_step_id: UUID | None
    severity: str
    message: str
    created_at: datetime


@dataclass(frozen=True)
class GuardrailCatalogItem:
    definition: GuardrailDefinition
    usage: GuardrailUsageSummary
    recent_failures: list[GuardrailFailure]


RUNTIME_GUARDRAIL_DEFINITIONS = [
    GuardrailDefinition(
        guardrail_type="prompt_injection",
        label="Prompt injection",
        description="Detects obvious attempts to override system or developer instructions.",
        stage="post-run governance evaluation",
        enabled=True,
        configurable=False,
        default_severity="high",
        action_on_fail="route_to_human_review",
        related_workflow_nodes=["route_review_or_finalize"],
    ),
    GuardrailDefinition(
        guardrail_type="citation_required",
        label="Citation required",
        description=(
            "Requires retrieved source citations before finalizing grounded support answers."
        ),
        stage="post-retrieval answer validation",
        enabled=True,
        configurable=False,
        default_severity="medium",
        action_on_fail="route_to_human_review",
        related_workflow_nodes=["retrieve_evidence", "route_review_or_finalize"],
    ),
    GuardrailDefinition(
        guardrail_type="unsupported_answer",
        label="Unsupported answer",
        description="Blocks answers when no retrieved evidence supports the response.",
        stage="post-retrieval answer validation",
        enabled=True,
        configurable=False,
        default_severity="high",
        action_on_fail="route_to_human_review",
        related_workflow_nodes=["retrieve_evidence", "route_review_or_finalize"],
    ),
    GuardrailDefinition(
        guardrail_type="confidence_threshold",
        label="Confidence threshold",
        description="Routes low-confidence outputs to review instead of finalizing automatically.",
        stage="routing decision",
        enabled=True,
        configurable=True,
        default_severity="medium",
        action_on_fail="route_to_human_review",
        related_workflow_nodes=["score_confidence", "route_review_or_finalize"],
    ),
    GuardrailDefinition(
        guardrail_type="language_preservation",
        label="Language preservation",
        description="Checks that generated answers preserve the detected user language.",
        stage="post-draft validation",
        enabled=True,
        configurable=False,
        default_severity="medium",
        action_on_fail="route_to_human_review",
        related_workflow_nodes=["draft_response", "route_review_or_finalize"],
    ),
    GuardrailDefinition(
        guardrail_type="model_provider_failure",
        label="Model provider failure",
        description="Routes model provider failures to review with the failure reason visible.",
        stage="model call failure handling",
        enabled=True,
        configurable=False,
        default_severity="high",
        action_on_fail="route_to_human_review",
        related_workflow_nodes=["classify_intent", "draft_response"],
    ),
    GuardrailDefinition(
        guardrail_type="model_budget_failure",
        label="Token budget failure",
        description="Routes token or context budget failures to review instead of overspending.",
        stage="token budget planning",
        enabled=True,
        configurable=True,
        default_severity="high",
        action_on_fail="route_to_human_review",
        related_workflow_nodes=["classify_intent", "draft_response"],
    ),
]


class GuardrailCatalogService:
    def __init__(self, db: Session):
        self.db = db

    def list_guardrails(self, *, workspace_id: UUID) -> list[GuardrailCatalogItem]:
        definitions_by_type = {
            definition.guardrail_type: definition for definition in RUNTIME_GUARDRAIL_DEFINITIONS
        }
        discovered_types = {
            guardrail_type
            for guardrail_type in self.db.scalars(
                select(GuardrailResult.guardrail_type)
                .where(GuardrailResult.workspace_id == workspace_id)
                .distinct()
            ).all()
        }
        for guardrail_type in sorted(discovered_types - definitions_by_type.keys()):
            definitions_by_type[guardrail_type] = _discovered_guardrail_definition(guardrail_type)

        return [
            GuardrailCatalogItem(
                definition=definition,
                usage=self._usage(
                    workspace_id=workspace_id,
                    guardrail_type=definition.guardrail_type,
                ),
                recent_failures=self._recent_failures(
                    workspace_id=workspace_id,
                    guardrail_type=definition.guardrail_type,
                ),
            )
            for definition in sorted(definitions_by_type.values(), key=lambda item: item.label)
        ]

    def _usage(self, *, workspace_id: UUID, guardrail_type: str) -> GuardrailUsageSummary:
        filters = (
            GuardrailResult.workspace_id == workspace_id,
            GuardrailResult.guardrail_type == guardrail_type,
        )
        total = self.db.scalar(select(func.count(GuardrailResult.id)).where(*filters)) or 0
        failed = self.db.scalar(
            select(func.count(GuardrailResult.id)).where(
                *filters, GuardrailResult.passed.is_(False)
            )
        ) or 0
        last_failed_at = self.db.scalar(
            select(func.max(GuardrailResult.created_at)).where(
                *filters, GuardrailResult.passed.is_(False)
            )
        )
        return GuardrailUsageSummary(
            total_evaluations=int(total),
            failed_evaluations=int(failed),
            pass_rate=round(((int(total) - int(failed)) / int(total)) if total else 0.0, 4),
            last_failed_at=last_failed_at,
        )

    def _recent_failures(
        self, *, workspace_id: UUID, guardrail_type: str
    ) -> list[GuardrailFailure]:
        failures = list(
            self.db.scalars(
                select(GuardrailResult)
                .where(
                    GuardrailResult.workspace_id == workspace_id,
                    GuardrailResult.guardrail_type == guardrail_type,
                    GuardrailResult.passed.is_(False),
                )
                .order_by(GuardrailResult.created_at.desc())
                .limit(8)
            ).all()
        )
        return [
            GuardrailFailure(
                id=failure.id,
                graph_run_id=failure.graph_run_id,
                graph_step_id=failure.graph_step_id,
                severity=failure.severity,
                message=failure.message,
                created_at=failure.created_at,
            )
            for failure in failures
        ]


def _discovered_guardrail_definition(guardrail_type: str) -> GuardrailDefinition:
    label = guardrail_type.replace("_", " ").title()
    return GuardrailDefinition(
        guardrail_type=guardrail_type,
        label=label,
        description="Runtime-discovered guardrail result from persisted workflow history.",
        stage="runtime governance",
        enabled=True,
        configurable=False,
        default_severity="medium",
        action_on_fail="inspect_trace",
        related_workflow_nodes=[],
    )
