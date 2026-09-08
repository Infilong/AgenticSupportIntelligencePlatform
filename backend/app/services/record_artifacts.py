"""Public projections of persisted step evidence; never expose arbitrary graph state."""

import json
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.trace_redaction import redact_trace
from app.models.agent import GraphRun, GraphStep
from app.models.task import SupportTask, TaskExecution
from app.services.graph_step_ordering import step_order

FIELDS = {
    "detect_language": ("detected_language", "language_source"),
    "classify_intent": ("intent", "sentiment", "product_area", "safety_risk",
                        "classification_confidence", "escalation_needed"),
    "retrieve_evidence": ("retrieved_chunks", "no_source"),
    "compress_context": ("packed_context_chunks", "trimmed_context_count"),
    "draft_response": ("draft_answer",),
    "score_confidence": ("confidence_score",),
    "route_review_or_finalize": ("route_decision", "route_reasons"),
    "finalize_response": ("final_answer",),
    "request_clarification": ("final_answer", "language_source"),
}
CHUNK_FIELDS = {"document_id", "document_title", "version", "chunk_index", "chunk_id",
                "content", "citation", "language", "vector_score", "lexical_score",
                "combined_score", "token_count"}


def list_artifacts(db: Session, *, workspace_id: UUID, record_id: UUID, run_id: UUID,
                   offset: int = 0, limit: int = 20) -> dict | None:
    execution = db.scalar(select(TaskExecution).join(GraphRun,
        GraphRun.id == TaskExecution.graph_run_id).join(SupportTask,
        SupportTask.id == TaskExecution.task_id).where(
        SupportTask.workspace_id == workspace_id,
        TaskExecution.workspace_id == workspace_id, TaskExecution.task_id == record_id,
        TaskExecution.graph_run_id == run_id, GraphRun.workspace_id == workspace_id))
    if execution is None:
        return None
    filters = (GraphStep.workspace_id == workspace_id, GraphStep.graph_run_id == run_id,
               GraphStep.step_name.in_(FIELDS))
    total = db.scalar(select(func.count()).select_from(GraphStep).where(*filters)) or 0
    steps = db.scalars(select(GraphStep).where(*filters).order_by(*step_order())
                       .offset(offset).limit(limit))
    items = []
    for step in steps:
        try:
            output = json.loads(step.output_json)
            if not isinstance(output, dict):
                raise ValueError("Invalid saved output")
        except (ValueError, RecursionError):
            items.append(dict(step_id=step.id, run_id=run_id, kind=step.step_name,
                created_at=step.created_at, status=step.status, data={},
                error="Saved artifact cannot be decoded."))
            continue
        data = {key: output[key] for key in FIELDS[step.step_name] if key in output}
        for key in ("retrieved_chunks", "packed_context_chunks"):
            if key in data:
                chunks = data[key]
                data[key] = [{k: v for k, v in chunk.items() if k in CHUNK_FIELDS}
                             for chunk in chunks if isinstance(chunk, dict)] if isinstance(
                                 chunks, list) else []
        items.append(dict(step_id=step.id, run_id=run_id, kind=step.step_name,
            created_at=step.created_at, status=step.status, data=redact_trace(data), error=None))
    return dict(items=items, total=total, offset=offset, limit=limit,
                has_next=offset + limit < total)
