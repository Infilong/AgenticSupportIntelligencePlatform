from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.agent import AgentConfig, GraphRun, GraphRunStatus, GraphStep
from app.models.user import User
from app.services.guardrails import GuardrailService, has_blocking_guardrail
from app.services.human_review_service import HumanReviewService
from app.services.support_agent_graph import SupportAgentGraphRunner, complete_graph_run
from app.services.support_agent_state import SupportAgentState


class AgentNotFoundError(ValueError):
    pass


class GraphRunNotFoundError(ValueError):
    pass


class AgentService:
    def __init__(self, db: Session):
        self.db = db

    def create_agent(self, *, workspace_id: UUID, name: str, token_budget: int) -> AgentConfig:
        agent = AgentConfig(workspace_id=workspace_id, name=name.strip(), token_budget=token_budget)
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def list_agents(self, *, workspace_id: UUID) -> list[AgentConfig]:
        return list(
            self.db.scalars(
                select(AgentConfig)
                .where(AgentConfig.workspace_id == workspace_id)
                .order_by(AgentConfig.created_at.desc())
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
            "user_id": str(current_user.id),
            "graph_run_id": str(graph_run.id),
            "input_message": input_message.strip(),
            "agent_token_budget": agent.token_budget,
            "agent_settings": _agent_settings(agent),
            "errors": [],
        }
        final_state = SupportAgentGraphRunner(self.db).run(state)
        graph_run = complete_graph_run(self.db, graph_run, final_state)
        decisions = GuardrailService(self.db).evaluate_and_store(
            workspace_id=workspace_id,
            graph_run_id=graph_run.id,
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


def _agent_settings(agent: AgentConfig) -> dict[str, Any]:
    try:
        loaded = json.loads(agent.settings_json or "{}")
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}
