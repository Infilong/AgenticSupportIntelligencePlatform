from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.agent import AgentConfig, GraphRun, GraphRunStatus, GraphStep
from app.models.ai import AIRun, ModelConfig
from app.models.evaluation import EvaluationResult, EvaluationRun
from app.models.user import User
from app.services.budget_policy_service import BudgetPolicyService
from app.services.guardrails import GuardrailService, has_blocking_guardrail
from app.services.human_review_service import HumanReviewService
from app.services.model_config_service import ModelConfigService
from app.services.support_agent_graph import SupportAgentGraphRunner, complete_graph_run
from app.services.support_agent_state import SupportAgentState


class AgentNotFoundError(ValueError):
    pass


class AgentUnavailableError(ValueError):
    pass


class AgentRateLimitExceededError(ValueError):
    pass


class AgentModelConfigNotFoundError(ValueError):
    pass


class GraphRunNotFoundError(ValueError):
    pass


class AgentService:
    def __init__(self, db: Session):
        self.db = db

    def create_agent(
        self,
        *,
        workspace_id: UUID,
        name: str,
        token_budget: int,
        model_config_id: UUID | None = None,
    ) -> AgentConfig:
        if model_config_id is not None:
            self._require_model_config(workspace_id=workspace_id, model_config_id=model_config_id)
        agent = AgentConfig(
            workspace_id=workspace_id,
            name=name.strip(),
            token_budget=token_budget,
            model_config_id=model_config_id,
        )
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def list_agents(
        self, *, workspace_id: UUID, include_archived: bool = False
    ) -> list[AgentConfig]:
        filters = [AgentConfig.workspace_id == workspace_id]
        if not include_archived:
            filters.append(AgentConfig.archived_at.is_(None))
        return list(
            self.db.scalars(
                select(AgentConfig).where(*filters).order_by(AgentConfig.created_at.desc())
            ).all()
        )

    def update_agent(
        self,
        *,
        workspace_id: UUID,
        agent_id: UUID,
        name: str | None = None,
        active: bool | None = None,
        token_budget: int | None = None,
        settings: dict[str, Any] | None = None,
        model_config_id: UUID | None = None,
        update_model_config: bool = False,
    ) -> AgentConfig:
        agent = self.get_agent(workspace_id=workspace_id, agent_id=agent_id)
        if agent is None:
            raise AgentNotFoundError("Agent was not found.")
        if name is not None:
            agent.name = name.strip()
        if active is not None:
            agent.active = active
        if token_budget is not None:
            agent.token_budget = token_budget
        if settings is not None:
            current_settings = _agent_settings(agent)
            current_settings.update(settings)
            agent.settings_json = json.dumps(current_settings, sort_keys=True)
        if update_model_config:
            if model_config_id is not None:
                self._require_model_config(
                    workspace_id=workspace_id, model_config_id=model_config_id
                )
            agent.model_config_id = model_config_id
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def run_agent(
        self,
        *,
        workspace_id: UUID,
        agent_id: UUID,
        input_message: str,
        current_user: User,
    ) -> GraphRun:
        agent = self.get_agent(workspace_id=workspace_id, agent_id=agent_id)
        if agent is None:
            raise AgentNotFoundError("Agent was not found.")
        if not agent.active or agent.archived_at is not None:
            raise AgentUnavailableError("Agent is inactive or archived.")
        budget_service = BudgetPolicyService(self.db)
        if budget_service.rate_limit_exceeded(workspace_id=workspace_id):
            raise AgentRateLimitExceededError("Workspace agent run rate limit exceeded.")
        effective_token_budget = budget_service.effective_run_token_budget(
            workspace_id=workspace_id, agent_token_budget=agent.token_budget
        )
        graph_run = GraphRun(
            workspace_id=workspace_id,
            agent_config_id=agent.id,
            user_id=current_user.id,
            input_message=input_message.strip(),
            status=GraphRunStatus.running,
        )
        self.db.add(graph_run)
        self.db.commit()
        self.db.refresh(graph_run)
        state: SupportAgentState = {
            "workspace_id": str(workspace_id),
            "agent_config_id": str(agent.id),
            "agent_model_config_id": str(agent.model_config_id) if agent.model_config_id else None,
            "user_id": str(current_user.id),
            "graph_run_id": str(graph_run.id),
            "input_message": input_message.strip(),
            "agent_token_budget": effective_token_budget,
            "agent_settings": _agent_settings(agent),
            "errors": [],
        }
        final_state = SupportAgentGraphRunner(self.db).run(state)
        graph_run = complete_graph_run(self.db, graph_run, final_state)
        route_step = self._latest_step(
            workspace_id=workspace_id,
            graph_run_id=graph_run.id,
            step_name="route_review_or_finalize",
        )
        decisions = GuardrailService(self.db).evaluate_and_store(
            workspace_id=workspace_id,
            graph_run_id=graph_run.id,
            graph_step_id=route_step.id if route_step else None,
            state=final_state,
        )
        if graph_run.status != GraphRunStatus.completed or has_blocking_guardrail(decisions):
            route_reasons = list(final_state.get("route_reasons", []))
            failed_types = [
                decision.guardrail_type for decision in decisions if not decision.passed
            ]
            review_reasons = sorted(set(route_reasons + failed_types))
            graph_run.status = GraphRunStatus.needs_human_review
            graph_run.route_decision = "human_review"
            graph_run.final_answer = None
            self.db.commit()
            self.db.refresh(graph_run)
            HumanReviewService(self.db).create_pending(
                workspace_id=workspace_id,
                graph_run_id=graph_run.id,
                reason=", ".join(review_reasons) or "human_review_route",
                proposed_answer=final_state.get("draft_answer"),
            )
        return graph_run

    def get_agent(self, *, workspace_id: UUID, agent_id: UUID) -> AgentConfig | None:
        return self.db.scalar(
            select(AgentConfig).where(
                AgentConfig.workspace_id == workspace_id,
                AgentConfig.id == agent_id,
            )
        )

    def archive_agent(self, *, workspace_id: UUID, agent_id: UUID) -> AgentConfig:
        agent = self.get_agent(workspace_id=workspace_id, agent_id=agent_id)
        if agent is None:
            raise AgentNotFoundError("Agent was not found.")
        agent.active = False
        if agent.archived_at is None:
            agent.archived_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def _latest_step(
        self, *, workspace_id: UUID, graph_run_id: UUID, step_name: str
    ) -> GraphStep | None:
        return self.db.scalar(
            select(GraphStep)
            .where(
                GraphStep.workspace_id == workspace_id,
                GraphStep.graph_run_id == graph_run_id,
                GraphStep.step_name == step_name,
            )
            .order_by(GraphStep.created_at.desc())
            .limit(1)
        )

    def get_run(self, *, workspace_id: UUID, run_id: UUID) -> GraphRun:
        run = self.db.scalar(
            select(GraphRun).where(GraphRun.workspace_id == workspace_id, GraphRun.id == run_id)
        )
        if run is None:
            raise GraphRunNotFoundError("Graph run was not found.")
        return run

    def get_trace(self, *, workspace_id: UUID, run_id: UUID) -> GraphRun:
        run = self.db.scalar(
            select(GraphRun)
            .options(selectinload(GraphRun.steps).selectinload(GraphStep.tool_calls))
            .where(GraphRun.workspace_id == workspace_id, GraphRun.id == run_id)
        )
        if run is None:
            raise GraphRunNotFoundError("Graph run was not found.")
        run.steps.sort(key=lambda step: step.created_at)
        return run

    def get_operational_summary(self, *, workspace_id: UUID, agent_id: UUID) -> dict[str, Any]:
        agent = self.get_agent(workspace_id=workspace_id, agent_id=agent_id)
        if agent is None:
            raise AgentNotFoundError("Agent was not found.")

        run_filter = (
            GraphRun.workspace_id == workspace_id,
            GraphRun.agent_config_id == agent_id,
        )
        run_ids = select(GraphRun.id).where(*run_filter)
        recent_runs = list(
            self.db.scalars(
                select(GraphRun).where(*run_filter).order_by(GraphRun.created_at.desc()).limit(8)
            ).all()
        )

        def scalar_int(statement) -> int:
            return int(self.db.scalar(statement) or 0)

        def scalar_float(statement) -> float:
            return float(self.db.scalar(statement) or 0.0)

        total_runs = scalar_int(select(func.count(GraphRun.id)).where(*run_filter))
        completed_runs = scalar_int(
            select(func.count(GraphRun.id)).where(
                *run_filter, GraphRun.status == GraphRunStatus.completed
            )
        )
        human_review_runs = scalar_int(
            select(func.count(GraphRun.id)).where(
                *run_filter, GraphRun.status == GraphRunStatus.needs_human_review
            )
        )
        failed_runs = scalar_int(
            select(func.count(GraphRun.id)).where(
                *run_filter, GraphRun.status == GraphRunStatus.failed
            )
        )
        total_tokens = scalar_int(
            select(func.coalesce(func.sum(AIRun.total_tokens), 0)).where(
                AIRun.workspace_id == workspace_id, AIRun.graph_run_id.in_(run_ids)
            )
        )
        total_estimated_cost = scalar_float(
            select(func.coalesce(func.sum(AIRun.estimated_cost), 0.0)).where(
                AIRun.workspace_id == workspace_id, AIRun.graph_run_id.in_(run_ids)
            )
        )
        average_latency = self.db.scalar(
            select(func.avg(AIRun.latency_ms)).where(
                AIRun.workspace_id == workspace_id, AIRun.graph_run_id.in_(run_ids)
            )
        )
        last_run_at = self.db.scalar(select(func.max(GraphRun.created_at)).where(*run_filter))
        evaluation_run_filter = (
            EvaluationRun.workspace_id == workspace_id,
            EvaluationRun.agent_config_id == agent_id,
            EvaluationRun.archived_at.is_(None),
        )
        evaluation_run_ids = select(EvaluationRun.id).where(*evaluation_run_filter)
        evaluation_runs = scalar_int(
            select(func.count(EvaluationRun.id)).where(*evaluation_run_filter)
        )
        evaluation_result_count = scalar_int(
            select(func.count(EvaluationResult.id)).where(
                EvaluationResult.workspace_id == workspace_id,
                EvaluationResult.evaluation_run_id.in_(evaluation_run_ids),
            )
        )
        failed_evaluation_results = scalar_int(
            select(func.count(EvaluationResult.id)).where(
                EvaluationResult.workspace_id == workspace_id,
                EvaluationResult.evaluation_run_id.in_(evaluation_run_ids),
                EvaluationResult.passed.is_(False),
            )
        )
        last_evaluation_at = self.db.scalar(
            select(func.max(EvaluationRun.completed_at)).where(*evaluation_run_filter)
        )
        evaluation_pass_rate = (
            round(
                (evaluation_result_count - failed_evaluation_results) / evaluation_result_count, 4
            )
            if evaluation_result_count
            else None
        )

        model_config = (
            self._get_model_config(workspace_id=workspace_id, model_config_id=agent.model_config_id)
            if agent.model_config_id
            else None
        )

        return {
            "agent": agent,
            "model_config": model_config,
            "recent_runs": recent_runs,
            "total_runs": total_runs,
            "completed_runs": completed_runs,
            "human_review_runs": human_review_runs,
            "failed_runs": failed_runs,
            "total_tokens": total_tokens,
            "total_estimated_cost": total_estimated_cost,
            "average_ai_latency_ms": (
                float(average_latency) if average_latency is not None else None
            ),
            "last_run_at": last_run_at,
            "evaluation_runs": evaluation_runs,
            "evaluation_result_count": evaluation_result_count,
            "failed_evaluation_results": failed_evaluation_results,
            "evaluation_pass_rate": evaluation_pass_rate,
            "last_evaluation_at": last_evaluation_at,
        }

    def get_workflow_summary(self, *, workspace_id: UUID, agent_id: UUID) -> dict[str, Any]:
        agent = self.get_agent(workspace_id=workspace_id, agent_id=agent_id)
        if agent is None:
            raise AgentNotFoundError("Agent was not found.")

        stats_rows = self.db.execute(
            select(
                GraphStep.step_name,
                func.count(GraphStep.id),
                func.coalesce(func.sum(case((GraphStep.status == "failed", 1), else_=0)), 0),
                func.avg(GraphStep.latency_ms),
                func.coalesce(func.sum(GraphStep.token_count), 0),
                func.coalesce(func.sum(GraphStep.estimated_cost), 0.0),
                func.max(GraphStep.created_at),
            )
            .join(GraphRun, GraphRun.id == GraphStep.graph_run_id)
            .where(
                GraphStep.workspace_id == workspace_id,
                GraphRun.workspace_id == workspace_id,
                GraphRun.agent_config_id == agent_id,
            )
            .group_by(GraphStep.step_name)
        ).all()
        stats_by_node = {row[0]: row for row in stats_rows}

        failure_rows = self.db.execute(
            select(GraphStep, GraphRun.id)
            .join(GraphRun, GraphRun.id == GraphStep.graph_run_id)
            .where(
                GraphStep.workspace_id == workspace_id,
                GraphRun.workspace_id == workspace_id,
                GraphRun.agent_config_id == agent_id,
                GraphStep.status == "failed",
            )
            .order_by(GraphStep.created_at.desc())
            .limit(20)
        ).all()
        failures_by_node: dict[str, list[dict[str, Any]]] = {}
        for step, graph_run_id in failure_rows:
            failures_by_node.setdefault(step.step_name, []).append(
                {
                    "graph_run_id": graph_run_id,
                    "graph_step_id": step.id,
                    "error_message": step.error_message,
                    "latency_ms": step.latency_ms,
                    "created_at": step.created_at,
                }
            )

        nodes = []
        for index, node in enumerate(_workflow_nodes(), start=1):
            row = stats_by_node.get(node["name"])
            nodes.append(
                {
                    **node,
                    "order": index,
                    "run_count": int(row[1]) if row else 0,
                    "failure_count": int(row[2]) if row else 0,
                    "average_latency_ms": float(row[3]) if row and row[3] is not None else None,
                    "total_tokens": int(row[4]) if row else 0,
                    "estimated_cost": float(row[5]) if row else 0.0,
                    "last_executed_at": row[6] if row else None,
                    "recent_failures": failures_by_node.get(node["name"], []),
                }
            )

        return {"agent": agent, "nodes": nodes, "edges": _workflow_edges()}

    def _get_model_config(
        self, *, workspace_id: UUID, model_config_id: UUID | None
    ) -> ModelConfig | None:
        if model_config_id is None:
            return None
        return ModelConfigService(self.db).get_config(
            workspace_id=workspace_id, model_config_id=model_config_id
        )

    def _require_model_config(self, *, workspace_id: UUID, model_config_id: UUID) -> ModelConfig:
        model_config = self._get_model_config(
            workspace_id=workspace_id, model_config_id=model_config_id
        )
        if model_config is None:
            raise AgentModelConfigNotFoundError("Model config was not found.")
        return model_config


def _workflow_nodes() -> list[dict[str, Any]]:
    return [
        {
            "name": "detect_language",
            "role": "deterministic language detection",
            "runtime_framework": "LangGraph StateGraph node",
            "uses_langchain": False,
            "expected_state_keys": ["input_message", "detected_language"],
        },
        {
            "name": "classify_intent",
            "role": "LangChain classification chain with cheap model config",
            "runtime_framework": "LangGraph StateGraph node",
            "uses_langchain": True,
            "expected_state_keys": [
                "intent",
                "sentiment",
                "product_area",
                "safety_risk",
                "classification_confidence",
            ],
        },
        {
            "name": "retrieve_evidence",
            "role": "LangChain retrieval tool plus persisted retrieval trace",
            "runtime_framework": "LangGraph StateGraph node",
            "uses_langchain": True,
            "expected_state_keys": ["retrieved_chunks", "retrieval_trace_id", "citations"],
        },
        {
            "name": "draft_response",
            "role": "LangChain grounded drafting chain with cited documents",
            "runtime_framework": "LangGraph StateGraph node",
            "uses_langchain": True,
            "expected_state_keys": ["draft_answer", "token_budget_action"],
        },
        {
            "name": "score_confidence",
            "role": "deterministic confidence scoring",
            "runtime_framework": "LangGraph StateGraph node",
            "uses_langchain": False,
            "expected_state_keys": ["confidence_score"],
        },
        {
            "name": "route_review_or_finalize",
            "role": "conditional LangGraph routing gate",
            "runtime_framework": "LangGraph StateGraph node",
            "uses_langchain": False,
            "expected_state_keys": ["route_decision", "route_reasons", "confidence_threshold"],
        },
        {
            "name": "finalize_response",
            "role": "final response commit",
            "runtime_framework": "LangGraph StateGraph node",
            "uses_langchain": False,
            "expected_state_keys": ["final_answer"],
        },
    ]


def _workflow_edges() -> list[dict[str, str | None]]:
    return [
        {
            "source": "START",
            "target": "detect_language",
            "condition": None,
            "label": "start",
        },
        {
            "source": "detect_language",
            "target": "classify_intent",
            "condition": None,
            "label": "next",
        },
        {
            "source": "classify_intent",
            "target": "retrieve_evidence",
            "condition": None,
            "label": "next",
        },
        {
            "source": "retrieve_evidence",
            "target": "draft_response",
            "condition": None,
            "label": "next",
        },
        {
            "source": "draft_response",
            "target": "score_confidence",
            "condition": None,
            "label": "next",
        },
        {
            "source": "score_confidence",
            "target": "route_review_or_finalize",
            "condition": None,
            "label": "next",
        },
        {
            "source": "route_review_or_finalize",
            "target": "finalize_response",
            "condition": "route_decision == finalize",
            "label": "finalize",
        },
        {
            "source": "route_review_or_finalize",
            "target": "END",
            "condition": "route_decision == human_review",
            "label": "human review",
        },
        {"source": "finalize_response", "target": "END", "condition": None, "label": "end"},
    ]


def _agent_settings(agent: AgentConfig) -> dict[str, Any]:
    try:
        loaded = json.loads(agent.settings_json or "{}")
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}
