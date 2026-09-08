"""Durable embedding admission, independent of document/retrieval transactions."""

import hashlib
import json
import math
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.agent import AgentConfig, GraphRun
from app.models.ai import AIRun, AIRunStatus
from app.models.budget import WorkspaceBudgetPolicy
from app.models.workspace import Workspace
from app.services.budget_reservations import BudgetReservationService
from app.services.execution_ownership import ExecutionOwner, own_execution


class EmbeddingAdmissionError(ValueError):
    pass


class EmbeddingAttemptLedger:
    def __init__(self, engine: Engine):
        # A caller-owned Connection can share/commit its transaction. Never accept one.
        if not isinstance(engine, Engine) or engine.dialect.name != "postgresql":
            raise ValueError("Durable embedding attempts require an independent PostgreSQL engine")
        self.engine = engine

    def execution(self, workspace_id: UUID):
        return own_execution(self.engine, workspace_id=workspace_id, execution_id=uuid4())

    def _session(self, workspace_id: UUID, owner: ExecutionOwner | None) -> Session:
        if owner is not None:
            if owner.workspace_id != workspace_id or owner.connection.engine is not self.engine:
                raise EmbeddingAdmissionError("Embedding execution owner does not match")
            if owner.connection.in_transaction():
                raise EmbeddingAdmissionError("Embedding ownership requires a clean transaction")
            # Enlist the Session before checking ownership, so its commit durably commits
            # the same connection transaction rather than joining an uncommitted outer one.
            db = Session(owner.connection)
            try:
                db.connection()
                owner.assert_owned()
            except Exception:
                db.close()
                raise
            return db
        return Session(self.engine)

    def begin(self, *, workspace_id: UUID, language: SupportedLanguage, model: str,
              texts: list[str], token_cost_per_1k: float, purpose: str,
              graph_run_id: UUID | None = None, owner: ExecutionOwner | None = None) -> UUID:
        if (not math.isfinite(token_cost_per_1k) or token_cost_per_1k <= 0
                or not texts or any(not isinstance(value, str) or not value for value in texts)
                or purpose not in {"embedding_document", "embedding_query"}):
            raise ValueError("Invalid embedding attempt metadata")
        estimate = sum(len(value.encode("utf-8")) for value in texts)
        cost = estimate * token_cost_per_1k / 1000
        now = datetime.now(UTC)
        with self._session(workspace_id, owner) as db:
            # NO KEY UPDATE serializes spending without blocking caller-owned FK key-share locks.
            workspace = db.scalar(select(Workspace).where(
                Workspace.id == workspace_id).with_for_update(key_share=True))
            if workspace is None or workspace.deleted_at or workspace.archived_at:
                raise EmbeddingAdmissionError("Embedding workspace is unavailable")
            policy = db.scalar(select(WorkspaceBudgetPolicy).where(
                WorkspaceBudgetPolicy.workspace_id == workspace_id))
            if policy is None:
                policy = WorkspaceBudgetPolicy(workspace_id=workspace_id)
                db.add(policy)
                db.flush()
            tokens, spent = BudgetReservationService(db).usage(workspace_id, now, since=
                now.replace(day=1, hour=0, minute=0, second=0, microsecond=0))
            if tokens + estimate > policy.monthly_token_budget:
                raise EmbeddingAdmissionError("monthly_token_budget_exceeded")
            if spent + cost > policy.monthly_cost_budget:
                raise EmbeddingAdmissionError("monthly_cost_budget_exceeded")
            if graph_run_id is not None:
                run = db.scalar(select(GraphRun).where(
                    GraphRun.workspace_id == workspace_id, GraphRun.id == graph_run_id))
                if run is None or purpose != "embedding_query":
                    raise EmbeddingAdmissionError("Embedding graph run was not found")
                agent = db.scalar(select(AgentConfig).where(
                    AgentConfig.workspace_id == workspace_id,
                    AgentConfig.id == run.agent_config_id))
                if agent is None:
                    raise EmbeddingAdmissionError("Embedding graph agent was not found")
                run_tokens, run_cost = BudgetReservationService(db).usage(
                    workspace_id, now, graph_run_id=graph_run_id)
                if run_tokens + estimate > min(agent.token_budget, policy.per_run_token_budget):
                    raise EmbeddingAdmissionError("token_budget_exceeded")
                if run_cost + cost > policy.per_run_cost_budget:
                    raise EmbeddingAdmissionError("cost_budget_exceeded")
            attempt = AIRun(workspace_id=workspace_id, provider="openai", model=model,
                execution_id=owner.execution_id if owner else None,
                execution_protocol="pg-session-v1" if owner else None,
                graph_run_id=graph_run_id,
                purpose=purpose, language=language, status=AIRunStatus.pending,
                rendered_prompt_hash=hashlib.sha256(json.dumps(texts, ensure_ascii=False,
                    separators=(",", ":")).encode("utf-8")).hexdigest(),
                prompt_tokens=estimate, completion_tokens=0, total_tokens=estimate,
                estimated_cost=cost, latency_ms=0, cache_hit=False,
                error_message="embedding_pending_usage_estimated")
            db.add(attempt)
            db.commit()
            return attempt.id

    def finish(self, *, workspace_id: UUID, attempt_id: UUID, prompt_tokens: int | None,
               latency_ms: int, owner: ExecutionOwner | None = None) -> None:
        if (type(latency_ms) is not int or latency_ms < 0 or (prompt_tokens is not None
                and (type(prompt_tokens) is not int or prompt_tokens < 1))):
            raise ValueError("Invalid embedding completion metadata")
        with self._session(workspace_id, owner) as db:
            # Same lock order as admission and graph reservation reconciliation.
            db.scalar(select(Workspace).where(Workspace.id == workspace_id)
                      .with_for_update(key_share=True))
            attempt = db.scalar(select(AIRun).where(
                AIRun.workspace_id == workspace_id, AIRun.id == attempt_id,
                AIRun.purpose.in_(["embedding_document", "embedding_query"])).with_for_update())
            if attempt is None:
                raise EmbeddingAdmissionError("Embedding attempt was not found")
            if attempt.execution_id is not None and (
                owner is None or owner.execution_id != attempt.execution_id
                or attempt.execution_protocol != "pg-session-v1"
            ):
                raise EmbeddingAdmissionError("Embedding execution owner does not match")
            if attempt.status != AIRunStatus.pending:
                raise EmbeddingAdmissionError("Embedding attempt is already finalized")
            attempt.latency_ms = latency_ms
            if prompt_tokens is None:
                attempt.status = AIRunStatus.uncertain
                attempt.error_message = "embedding_usage_unknown_requires_reconciliation"
            else:
                rate = attempt.estimated_cost / attempt.total_tokens
                exceeds_estimate = prompt_tokens > attempt.total_tokens
                attempt.prompt_tokens = attempt.total_tokens = prompt_tokens
                attempt.estimated_cost = prompt_tokens * rate
                attempt.status = (AIRunStatus.uncertain if exceeds_estimate
                                  else AIRunStatus.succeeded)
                attempt.error_message = ("embedding_usage_exceeded_admission_estimate"
                                         if exceeds_estimate else None)
            db.commit()
