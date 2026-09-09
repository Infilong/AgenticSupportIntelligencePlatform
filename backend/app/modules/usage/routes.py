"""Bounded workspace usage aggregates with explicit unknown measurements."""

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import aggregate_order_by

from app.modules.identity.dependencies import CurrentUser, Database
from app.modules.usage.models import ModelCall
from app.modules.workspaces.service import membership

router = APIRouter(prefix="/api/workspaces/{workspace_id}/usage", tags=["usage"])


class UsageTotals(BaseModel):
    calls: int
    succeeded: int
    failed: int
    uncertain: int
    started: int
    input_tokens: int
    missing_tokens: int
    recorded_cost_usd: float
    missing_cost: int
    recorded_duration_ms: float
    missing_duration: int


class ModelUsage(UsageTotals):
    operation: str
    provider: str
    model: str
    revision: str


class UsageReport(BaseModel):
    since: datetime
    until: datetime
    days: int
    totals: UsageTotals
    models: list[ModelUsage]
    more_models: bool


def metrics():
    return [
        func.count().label("calls"),
        *(
            func.count().filter(ModelCall.status == state).label(state)
            for state in ("succeeded", "failed", "uncertain", "started")
        ),
        func.coalesce(func.sum(ModelCall.input_tokens), 0).label("input_tokens"),
        func.count().filter(ModelCall.input_tokens.is_(None)).label("missing_tokens"),
        func.coalesce(func.sum(ModelCall.api_cost_usd), 0).label("recorded_cost_usd"),
        func.count().filter(ModelCall.api_cost_usd.is_(None)).label("missing_cost"),
        func.coalesce(func.sum(ModelCall.duration_ms), 0).label("recorded_duration_ms"),
        func.count().filter(ModelCall.duration_ms.is_(None)).label("missing_duration"),
    ]


@router.get("", response_model=UsageReport)
def usage(workspace_id: UUID, user: CurrentUser, db: Database, days: int = Query(7, ge=1, le=90)):
    membership(db, workspace_id, user.id)
    until = db.scalar(select(func.clock_timestamp()))
    since = until - timedelta(days=days)
    # One SQL statement gives totals and model groups the same MVCC snapshot.
    scope = (
        ModelCall.workspace_id == workspace_id,
        ModelCall.created_at >= since,
        ModelCall.created_at < until,
    )
    totals = select(*metrics()).where(*scope).cte("usage_totals")
    groups = [ModelCall.operation, ModelCall.provider, ModelCall.model, ModelCall.revision]
    grouped = (
        select(*groups, *metrics())
        .where(*scope)
        .group_by(*groups)
        .order_by(func.count().desc(), *groups)
        .limit(21)
        .cte("usage_models")
    )
    rows = select(
        func.jsonb_agg(
            aggregate_order_by(
                func.to_jsonb(grouped.table_valued()),
                grouped.c.calls.desc(),
                grouped.c.operation,
                grouped.c.provider,
                grouped.c.model,
                grouped.c.revision,
            )
        )
    ).scalar_subquery()
    result = db.execute(select(*totals.c, rows.label("models"))).mappings().one()
    models = result["models"] or []
    return {
        "since": since,
        "until": until,
        "days": days,
        "totals": {key: result[key] for key in totals.c.keys()},
        "models": models[:20],
        "more_models": len(models) > 20,
    }
