from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.guardrail import GuardrailPolicy
from app.models.review import GuardrailResult


class GuardrailPolicyNotFoundError(ValueError):
    pass


class GuardrailPolicyNotConfigurableError(ValueError):
    pass


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
    threshold: float | None = None


@dataclass(frozen=True)
class GuardrailEffectivePolicy:
    guardrail_type: str
    enabled: bool
    severity: str
    action_on_fail: str
    threshold: float | None


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
    policy: GuardrailEffectivePolicy
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
        guardrail_type="privacy_complaint",
        label="Privacy complaint",
        description="Escalates messages reporting possible personal data exposure or privacy harm.",
        stage="classification routing",
        enabled=True,
        configurable=False,
        default_severity="high",
        action_on_fail="route_to_human_review",
        related_workflow_nodes=["classify_intent", "route_review_or_finalize"],
    ),
    GuardrailDefinition(
        guardrail_type="high_safety_risk",
        label="High safety risk",
        description="Escalates high-risk safety classifications before finalization.",
        stage="classification routing",
        enabled=True,
        configurable=False,
        default_severity="high",
        action_on_fail="route_to_human_review",
        related_workflow_nodes=["classify_intent", "route_review_or_finalize"],
    ),
    GuardrailDefinition(
        guardrail_type="escalation_needed",
        label="Escalation needed",
        description="Routes business-critical escalations to human review.",
        stage="classification routing",
        enabled=True,
        configurable=True,
        default_severity="medium",
        action_on_fail="route_to_human_review",
        related_workflow_nodes=["classify_intent", "route_review_or_finalize"],
    ),
    GuardrailDefinition(
        guardrail_type="citation_required",
        label="Citation required",
        description=(
            "Requires retrieved source citations before finalizing grounded support answers."
        ),
        stage="post-retrieval answer validation",
        enabled=True,
        configurable=True,
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
        configurable=True,
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
        configurable=True,
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

    def list_guardrails(
        self,
        *,
        workspace_id: UUID,
        search: str | None = None,
        view: str = "all",
        limit: int = 30,
        offset: int = 0,
    ) -> list[GuardrailCatalogItem]:
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

        policies = self.effective_policies(workspace_id=workspace_id)
        items = [
            GuardrailCatalogItem(
                definition=definition,
                policy=policies.get(definition.guardrail_type)
                or _effective_policy(definition, None),
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
        filtered = [
            item
            for item in items
            if _guardrail_matches_view(item, view) and _guardrail_matches_search(item, search)
        ]
        start = max(offset, 0)
        return filtered[start : start + _bounded_limit(limit)]

    def effective_policies(self, *, workspace_id: UUID) -> dict[str, GuardrailEffectivePolicy]:
        definitions = {
            definition.guardrail_type: definition for definition in RUNTIME_GUARDRAIL_DEFINITIONS
        }
        stored = {
            policy.guardrail_type: policy
            for policy in self.db.scalars(
                select(GuardrailPolicy).where(GuardrailPolicy.workspace_id == workspace_id)
            ).all()
        }
        return {
            guardrail_type: _effective_policy(definition, stored.get(guardrail_type))
            for guardrail_type, definition in definitions.items()
        }

    def update_policy(
        self,
        *,
        workspace_id: UUID,
        guardrail_type: str,
        enabled: bool,
        severity: str,
        action_on_fail: str,
        threshold: float | None,
    ) -> GuardrailCatalogItem:
        definition = _definition_for_update(guardrail_type)
        if threshold is not None and guardrail_type != "confidence_threshold":
            raise GuardrailPolicyNotConfigurableError(
                "Threshold is only supported for the confidence_threshold guardrail."
            )
        policy = self.db.scalar(
            select(GuardrailPolicy).where(
                GuardrailPolicy.workspace_id == workspace_id,
                GuardrailPolicy.guardrail_type == guardrail_type,
            )
        )
        if policy is None:
            policy = GuardrailPolicy(
                workspace_id=workspace_id,
                guardrail_type=guardrail_type,
                enabled=enabled,
                severity=severity,
                action_on_fail=action_on_fail,
                threshold=threshold,
            )
            self.db.add(policy)
        else:
            policy.enabled = enabled
            policy.severity = severity
            policy.action_on_fail = action_on_fail
            policy.threshold = threshold
        self.db.commit()
        self.db.refresh(policy)
        effective = _effective_policy(definition, policy)
        return GuardrailCatalogItem(
            definition=definition,
            policy=effective,
            usage=self._usage(workspace_id=workspace_id, guardrail_type=definition.guardrail_type),
            recent_failures=self._recent_failures(
                workspace_id=workspace_id, guardrail_type=definition.guardrail_type
            ),
        )

    def _usage(self, *, workspace_id: UUID, guardrail_type: str) -> GuardrailUsageSummary:
        filters = (
            GuardrailResult.workspace_id == workspace_id,
            GuardrailResult.guardrail_type == guardrail_type,
        )
        total = self.db.scalar(select(func.count(GuardrailResult.id)).where(*filters)) or 0
        failed = (
            self.db.scalar(
                select(func.count(GuardrailResult.id)).where(
                    *filters, GuardrailResult.passed.is_(False)
                )
            )
            or 0
        )
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


def _definition_for_update(guardrail_type: str) -> GuardrailDefinition:
    for definition in RUNTIME_GUARDRAIL_DEFINITIONS:
        if definition.guardrail_type == guardrail_type:
            if not definition.configurable:
                raise GuardrailPolicyNotConfigurableError(
                    f"{guardrail_type} is a fixed runtime guardrail."
                )
            return definition
    raise GuardrailPolicyNotFoundError("Guardrail policy was not found.")


def _effective_policy(
    definition: GuardrailDefinition, policy: GuardrailPolicy | None
) -> GuardrailEffectivePolicy:
    return GuardrailEffectivePolicy(
        guardrail_type=definition.guardrail_type,
        enabled=policy.enabled if policy is not None else definition.enabled,
        severity=policy.severity if policy is not None else definition.default_severity,
        action_on_fail=policy.action_on_fail if policy is not None else definition.action_on_fail,
        threshold=policy.threshold if policy is not None else definition.threshold,
    )


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


def _bounded_limit(limit: int) -> int:
    return max(min(limit, 100), 1)


def _guardrail_matches_view(item: GuardrailCatalogItem, view: str) -> bool:
    definition = item.definition
    policy = item.policy
    if view == "failed":
        return item.usage.failed_evaluations > 0
    if view == "configurable":
        return definition.configurable
    if view == "fixed":
        return not definition.configurable
    if view == "routing":
        return policy.action_on_fail != "record_only"
    return True


def _guardrail_matches_search(item: GuardrailCatalogItem, search: str | None) -> bool:
    query = (search or "").strip().lower()
    if not query:
        return True
    definition = item.definition
    policy = item.policy
    haystack = " ".join(
        [
            definition.guardrail_type,
            definition.label,
            definition.description,
            definition.stage,
            definition.default_severity,
            policy.severity,
            policy.action_on_fail,
            *definition.related_workflow_nodes,
            *[failure.severity for failure in item.recent_failures],
            *[failure.message for failure in item.recent_failures],
        ]
    ).lower()
    return query in haystack
