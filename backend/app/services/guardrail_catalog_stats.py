"""Workspace-scoped aggregate statistics and bounded recent guardrail failures."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.review import GuardrailResult


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


EMPTY_USAGE = GuardrailUsageSummary(0, 0, 0.0, None)


def catalog_usage(db: Session, workspace_id: UUID) -> dict[str, GuardrailUsageSummary]:
    failed = GuardrailResult.passed.is_(False)
    rows = db.execute(select(
        GuardrailResult.guardrail_type, func.count(GuardrailResult.id),
        func.count(GuardrailResult.id).filter(failed),
        func.max(GuardrailResult.created_at).filter(failed),
    ).where(GuardrailResult.workspace_id == workspace_id)
        .group_by(GuardrailResult.guardrail_type)).all()
    return {kind: GuardrailUsageSummary(total, failures, round((total - failures) / total, 4), last)
            for kind, total, failures, last in rows}


def catalog_failures(db: Session, workspace_id: UUID) -> dict[str, list[GuardrailFailure]]:
    ranked = select(
        GuardrailResult.id,
        func.row_number().over(partition_by=GuardrailResult.guardrail_type,
            order_by=(GuardrailResult.created_at.desc(), GuardrailResult.id.desc())).label("rank"),
    ).where(GuardrailResult.workspace_id == workspace_id,
            GuardrailResult.passed.is_(False)).subquery()
    rows = db.scalars(select(GuardrailResult).join(ranked, ranked.c.id == GuardrailResult.id)
        .where(ranked.c.rank <= 8, GuardrailResult.workspace_id == workspace_id)
        .order_by(GuardrailResult.created_at.desc(), GuardrailResult.id.desc())).all()
    result: dict[str, list[GuardrailFailure]] = {}
    for row in rows:
        result.setdefault(row.guardrail_type, []).append(GuardrailFailure(
            id=row.id, graph_run_id=row.graph_run_id, graph_step_id=row.graph_step_id,
            severity=row.severity, message=row.message, created_at=row.created_at,
        ))
    return result
