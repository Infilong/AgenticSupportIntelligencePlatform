"""Persist serial workflow step order; nullable sequence identifies legacy history."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import GraphRun, GraphStep


def step_order(*, descending: bool = False):
    """Legacy rows precede sequenced rows; timestamp/ID fallback is not causal proof."""
    if descending:
        return (GraphStep.sequence.desc().nulls_last(),
                GraphStep.created_at.desc(), GraphStep.id.desc())
    return (GraphStep.sequence.asc().nulls_first(),
            GraphStep.created_at.asc(), GraphStep.id.asc())


def step_sort_key(step: GraphStep):
    return (step.sequence is not None, step.sequence or 0, step.created_at, step.id)


def persist_step(db: Session, step: GraphStep, *, commit: bool = True) -> None:
    """Serialize step order; action transactions may flush without committing early."""
    try:
        run_id = db.scalar(select(GraphRun.id).where(
            GraphRun.id == step.graph_run_id, GraphRun.workspace_id == step.workspace_id,
        ).with_for_update(key_share=True))
        if run_id is None:
            raise ValueError("Graph run is unavailable in this workspace.")
        previous = db.scalar(select(GraphStep).where(
            GraphStep.graph_run_id == run_id, GraphStep.workspace_id == step.workspace_id,
        ).order_by(*step_order(descending=True)).limit(1))
        step.sequence = (previous.sequence or 0) + 1 if previous else 1
        step.parent_span_id = previous.span_id if previous else None
        db.add(step)
        if commit:
            db.commit()
        else:
            db.flush()
    except Exception:
        db.rollback()
        raise
    db.refresh(step)
