"""Read model usage from the scoped ledger rather than lossy graph step summaries."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai import AIRun


def graph_model_usage(db: Session, workspace_id: UUID, graph_run_id: UUID) -> tuple[int, float]:
    prompt_tokens, cost = db.execute(select(
        func.coalesce(func.sum(AIRun.prompt_tokens), 0),
        func.coalesce(func.sum(AIRun.estimated_cost), 0.0),
    ).where(AIRun.workspace_id == workspace_id, AIRun.graph_run_id == graph_run_id)).one()
    return int(prompt_tokens), float(cost)
