from __future__ import annotations

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
            failed_types = [
                decision.guardrail_type for decision in decisions if not decision.passed
            ]
            graph_run.status = GraphRunStatus.needs_human_review
            graph_run.route_decision = "human_review"
            graph_run.final_answer = None
            self.db.commit()
            self.db.refresh(graph_run)
            HumanReviewService(self.db).create_pending(
                workspace_id=workspace_id,
                graph_run_id=graph_run.id,
                reason=", ".join(failed_types) or "human_review_route",
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
