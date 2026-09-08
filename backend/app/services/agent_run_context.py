"""Create the persisted run and its initial graph context."""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.core.workflow_logging import log_graph_created
from app.models.agent import AgentConfig, GraphRun, GraphRunStatus
from app.models.user import User
from app.services.support_agent_state import SupportAgentState


def prepare_agent_run(db: Session, *, workspace_id: UUID, agent: AgentConfig, current_user: User,
                      input_message: str, token_budget: int, settings: dict[str, Any],
                      language: str | None = None, commit: bool = True
                      ) -> tuple[GraphRun, SupportAgentState]:
    selected_language = SupportedLanguage(language).value if language is not None else None
    graph_run = GraphRun(
        workspace_id=workspace_id,
        agent_config_id=agent.id,
        user_id=current_user.id,
        input_message=input_message.strip(),
        status=GraphRunStatus.running,
    )
    db.add(graph_run)
    if commit:
        db.commit()
        db.refresh(graph_run)
    else:
        db.flush()
    log_graph_created(graph_run.id, graph_run.trace_id)
    state: SupportAgentState = {
        "workspace_id": str(workspace_id),
        "agent_config_id": str(agent.id),
        "agent_model_config_id": str(agent.model_config_id) if agent.model_config_id else None,
        "user_id": str(current_user.id),
        "graph_run_id": str(graph_run.id),
        "input_message": input_message.strip(),
        "requested_language": selected_language,
        "agent_token_budget": token_budget,
        "agent_settings": settings,
        "errors": [],
    }
    return graph_run, state
