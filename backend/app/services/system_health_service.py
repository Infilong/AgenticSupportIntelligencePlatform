from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.agent import AgentConfig, GraphRun, GraphRunStatus, ToolCall
from app.models.ai import AIRun, AIRunStatus, ModelConfig, PromptTemplate
from app.models.audit import AuditLog
from app.models.dataset import ConversationExample, Dataset
from app.models.evaluation import EvaluationRun, EvaluationRunStatus
from app.models.folder import ResourceFolder
from app.models.knowledge import DocumentStatus, KnowledgeDocument
from app.models.review import GuardrailResult, HumanReview, ReviewDecision
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.schemas.system_health import (
    HealthStatus,
    SystemHealthCheck,
    SystemHealthMetric,
    SystemHealthResponse,
    SystemHealthSection,
)
from app.services.budget_policy_service import BudgetPolicyService


class SystemHealthService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def get_workspace_health(self, *, workspace_id: UUID) -> SystemHealthResponse:
        checks = self._runtime_checks(workspace_id=workspace_id)
        sections = [
            self._provider_section(workspace_id=workspace_id),
            self._budget_section(workspace_id=workspace_id),
            self._operations_section(workspace_id=workspace_id),
            self._data_section(workspace_id=workspace_id),
            self._governance_section(workspace_id=workspace_id),
        ]
        overall_status = self._rollup(
            [check.status for check in checks] + [section.status for section in sections]
        )
        return SystemHealthResponse(
            workspace_id=workspace_id,
            generated_at=datetime.now(UTC),
            overall_status=overall_status,
            checks=checks,
            sections=sections,
        )

    def _runtime_checks(self, *, workspace_id: UUID) -> list[SystemHealthCheck]:
        checks = [
            SystemHealthCheck(
                id="api",
                label="API",
                status="ok",
                message=(
                    "Workspace health endpoint is responding with authenticated workspace access."
                ),
            )
        ]
        try:
            self.db.execute(text("select 1")).scalar_one()
            checks.append(
                SystemHealthCheck(
                    id="database",
                    label="Database",
                    status="ok",
                    message="Database session executed a live select.",
                )
            )
        except Exception as exc:  # pragma: no cover - defensive runtime health reporting
            checks.append(
                SystemHealthCheck(
                    id="database",
                    label="Database",
                    status="critical",
                    message=f"Database check failed: {exc}",
                )
            )
        redis_status: HealthStatus = "warning" if self.settings.redis_url else "not_configured"
        redis_message = (
            "Redis URL is configured, but this local build does not include "
            "a live Redis ping client yet."
            if self.settings.redis_url
            else "Redis URL is not configured."
        )
        checks.append(
            SystemHealthCheck(
                id="redis", label="Redis/worker", status=redis_status, message=redis_message
            )
        )
        return checks

    def _provider_section(self, *, workspace_id: UUID) -> SystemHealthSection:
        total = self._count(ModelConfig, ModelConfig.workspace_id == workspace_id)
        active = self._count(
            ModelConfig, ModelConfig.workspace_id == workspace_id, ModelConfig.active.is_(True)
        )
        live_active = self._count(
            ModelConfig,
            ModelConfig.workspace_id == workspace_id,
            ModelConfig.active.is_(True),
            ModelConfig.provider != "mock",
        )
        has_api_key = bool(self.settings.openai_api_key)
        if active == 0:
            status: HealthStatus = "warning"
            summary = "No active model configs are available for agent routing."
        elif live_active > 0 and not has_api_key:
            status = "warning"
            summary = "Live provider routes are active but OPENAI_API_KEY is not configured."
        else:
            status = "ok"
            summary = "Model routing is configured for this workspace."
        return SystemHealthSection(
            id="providers",
            title="Model provider readiness",
            status=status,
            summary=summary,
            metrics=[
                SystemHealthMetric(label="Model configs", value=total),
                SystemHealthMetric(
                    label="Active configs", value=active, status="warning" if active == 0 else "ok"
                ),
                SystemHealthMetric(
                    label="Live provider routes",
                    value=live_active,
                    status="warning" if live_active > 0 and not has_api_key else "ok",
                    detail="Non-mock providers require a configured API key.",
                ),
                SystemHealthMetric(
                    label="OpenAI key",
                    value="configured" if has_api_key else "missing",
                    status="ok" if has_api_key or live_active == 0 else "warning",
                ),
            ],
        )

    def _budget_section(self, *, workspace_id: UUID) -> SystemHealthSection:
        agent_count = self._count(
            AgentConfig, AgentConfig.workspace_id == workspace_id, AgentConfig.archived_at.is_(None)
        )
        budgets = list(
            self.db.scalars(
                select(AgentConfig.token_budget).where(
                    AgentConfig.workspace_id == workspace_id, AgentConfig.archived_at.is_(None)
                )
            ).all()
        )
        max_context = (
            self.db.scalar(
                select(func.max(ModelConfig.max_context_tokens)).where(
                    ModelConfig.workspace_id == workspace_id, ModelConfig.active.is_(True)
                )
            )
            or 0
        )
        avg_budget = round(sum(budgets) / len(budgets)) if budgets else 0
        budget_service = BudgetPolicyService(self.db)
        policy = budget_service.get_or_create(workspace_id=workspace_id)
        usage = budget_service.current_month_usage(workspace_id=workspace_id)
        status: HealthStatus = "warning" if usage.alerting or agent_count == 0 else "ok"
        token_status: HealthStatus = (
            "warning"
            if usage.token_budget_used_percent >= policy.alert_threshold_percent
            else "ok"
        )
        cost_status: HealthStatus = (
            "warning"
            if usage.cost_budget_used_percent >= policy.alert_threshold_percent
            else "ok"
        )
        return SystemHealthSection(
            id="budgets",
            title="Budgets and limits",
            status=status,
            summary=(
                "Workspace budget policy is configured and enforced on agent run rate/token caps."
                if agent_count
                else "Create an agent to enforce token budgets on graph runs."
            ),
            metrics=[
                SystemHealthMetric(label="Active agents", value=agent_count, status=status),
                SystemHealthMetric(label="Average token budget", value=avg_budget),
                SystemHealthMetric(label="Largest model context", value=max_context),
                SystemHealthMetric(
                    label="Monthly token budget",
                    value=policy.monthly_token_budget,
                    status=token_status,
                    detail=f"{usage.tokens} tokens used this month.",
                ),
                SystemHealthMetric(
                    label="Monthly cost budget",
                    value=f"${policy.monthly_cost_budget:.2f}",
                    status=cost_status,
                    detail=f"${usage.estimated_cost:.4f} estimated cost this month.",
                ),
                SystemHealthMetric(
                    label="Per-run token cap",
                    value=policy.per_run_token_budget,
                    detail=(
                        "The runtime uses the lower of the agent budget and "
                        "workspace per-run cap."
                    ),
                ),
                SystemHealthMetric(
                    label="Rate limits",
                    value=f"{policy.rate_limit_requests_per_hour}/hour",
                    detail=(
                        "Agent run creation is blocked once this workspace hourly "
                        "request limit is reached."
                    ),
                ),
            ],
        )

    def _operations_section(self, *, workspace_id: UUID) -> SystemHealthSection:
        pending_reviews = self._count(
            HumanReview,
            HumanReview.workspace_id == workspace_id,
            HumanReview.reviewer_decision == ReviewDecision.pending,
        )
        failed_graph_runs = self._count(
            GraphRun,
            GraphRun.workspace_id == workspace_id,
            GraphRun.status == GraphRunStatus.failed,
        )
        failed_ai_runs = self._count(
            AIRun, AIRun.workspace_id == workspace_id, AIRun.status == AIRunStatus.failed
        )
        failed_evaluations = self._count(
            EvaluationRun,
            EvaluationRun.workspace_id == workspace_id,
            EvaluationRun.status == EvaluationRunStatus.failed,
        )
        failed_tools = self._count(
            ToolCall, ToolCall.workspace_id == workspace_id, ToolCall.status == "failed"
        )
        failed_documents = self._count(
            KnowledgeDocument,
            KnowledgeDocument.workspace_id == workspace_id,
            KnowledgeDocument.status == DocumentStatus.failed,
        )
        risk_count = (
            pending_reviews
            + failed_graph_runs
            + failed_ai_runs
            + failed_evaluations
            + failed_tools
            + failed_documents
        )
        status: HealthStatus = (
            "critical" if failed_graph_runs or failed_ai_runs else "warning" if risk_count else "ok"
        )
        return SystemHealthSection(
            id="operations",
            title="Operational risks",
            status=status,
            summary="Operational queues and failures that need operator attention.",
            metrics=[
                SystemHealthMetric(
                    label="Pending human reviews",
                    value=pending_reviews,
                    status="warning" if pending_reviews else "ok",
                ),
                SystemHealthMetric(
                    label="Failed graph runs",
                    value=failed_graph_runs,
                    status="critical" if failed_graph_runs else "ok",
                ),
                SystemHealthMetric(
                    label="Failed AI runs",
                    value=failed_ai_runs,
                    status="critical" if failed_ai_runs else "ok",
                ),
                SystemHealthMetric(
                    label="Failed tool calls",
                    value=failed_tools,
                    status="warning" if failed_tools else "ok",
                ),
                SystemHealthMetric(
                    label="Failed evaluations",
                    value=failed_evaluations,
                    status="warning" if failed_evaluations else "ok",
                ),
                SystemHealthMetric(
                    label="Failed documents",
                    value=failed_documents,
                    status="warning" if failed_documents else "ok",
                ),
            ],
        )

    def _data_section(self, *, workspace_id: UUID) -> SystemHealthSection:
        docs = self._count(KnowledgeDocument, KnowledgeDocument.workspace_id == workspace_id)
        indexed_docs = self._count(
            KnowledgeDocument,
            KnowledgeDocument.workspace_id == workspace_id,
            KnowledgeDocument.status == DocumentStatus.indexed,
        )
        datasets = self._count(Dataset, Dataset.workspace_id == workspace_id)
        examples = self._count(
            ConversationExample, ConversationExample.workspace_id == workspace_id
        )
        folders = self._count(ResourceFolder, ResourceFolder.workspace_id == workspace_id)
        status: HealthStatus = "warning" if docs == 0 or datasets == 0 else "ok"
        return SystemHealthSection(
            id="data",
            title="Data and retrieval readiness",
            status=status,
            summary="Knowledge and evaluation data available to RAG, labels, and evaluations.",
            metrics=[
                SystemHealthMetric(
                    label="Documents", value=docs, status="warning" if docs == 0 else "ok"
                ),
                SystemHealthMetric(
                    label="Indexed documents",
                    value=indexed_docs,
                    status="warning" if docs and indexed_docs == 0 else "ok",
                ),
                SystemHealthMetric(
                    label="Datasets", value=datasets, status="warning" if datasets == 0 else "ok"
                ),
                SystemHealthMetric(label="Conversation examples", value=examples),
                SystemHealthMetric(label="Resource folders", value=folders),
            ],
        )

    def _governance_section(self, *, workspace_id: UUID) -> SystemHealthSection:
        members = self._count(WorkspaceMember, WorkspaceMember.workspace_id == workspace_id)
        owners = self._count(
            WorkspaceMember,
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.role == WorkspaceRole.owner,
        )
        guardrail_failures = self._count(
            GuardrailResult,
            GuardrailResult.workspace_id == workspace_id,
            GuardrailResult.passed.is_(False),
        )
        active_prompts = self._count(
            PromptTemplate,
            PromptTemplate.workspace_id == workspace_id,
            PromptTemplate.active.is_(True),
        )
        audit_events = self._count(AuditLog, AuditLog.workspace_id == workspace_id)
        status: HealthStatus = (
            "critical" if owners == 0 else "warning" if guardrail_failures else "ok"
        )
        return SystemHealthSection(
            id="governance",
            title="Governance and audit",
            status=status,
            summary="Workspace ownership, prompt governance, guardrails, and auditability.",
            metrics=[
                SystemHealthMetric(label="Members", value=members),
                SystemHealthMetric(
                    label="Owners", value=owners, status="critical" if owners == 0 else "ok"
                ),
                SystemHealthMetric(label="Active prompts", value=active_prompts),
                SystemHealthMetric(
                    label="Guardrail failures",
                    value=guardrail_failures,
                    status="warning" if guardrail_failures else "ok",
                ),
                SystemHealthMetric(label="Audit events", value=audit_events),
            ],
        )

    def _count(self, model: type, *conditions) -> int:
        return int(self.db.scalar(select(func.count()).select_from(model).where(*conditions)) or 0)

    def _rollup(self, statuses: list[HealthStatus]) -> HealthStatus:
        if "critical" in statuses:
            return "critical"
        if "warning" in statuses:
            return "warning"
        if statuses and all(status == "not_configured" for status in statuses):
            return "not_configured"
        return "ok"
