from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query
from sqlalchemy import select

from app.jobs.queue import authorize
from app.modules.comparisons import reading, service
from app.modules.comparisons.models import Comparison
from app.modules.comparisons.schemas import (
    ComparisonCreated,
    ComparisonDetail,
    ComparisonInput,
    ComparisonList,
)
from app.modules.identity.dependencies import CurrentUser, Database
from app.modules.workspaces.service import membership

router = APIRouter(prefix="/api/workspaces/{workspace_id}/comparisons", tags=["comparisons"])


@router.post("", status_code=202, response_model=ComparisonCreated)
def create(
    workspace_id: UUID,
    data: ComparisonInput,
    user: CurrentUser,
    db: Database,
    key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=100)],
):
    identity = service.create(db, workspace_id, user.id, data, key)
    db.commit()
    return {"id": identity}


@router.get("", response_model=ComparisonList)
def listing(workspace_id: UUID, user: CurrentUser, db: Database, offset: int = Query(0, ge=0, le=1000)):
    authorize(db, workspace_id, user.id)
    membership(db, workspace_id, user.id, {"admin"})
    rows = db.scalars(
        select(Comparison)
        .where(Comparison.workspace_id == workspace_id)
        .order_by(Comparison.created_at.desc(), Comparison.id)
        .offset(offset)
        .limit(20)
    )
    return {
        "items": [
            {"id": row.id, "question": row.question, "language": row.language, "cancelled": row.cancelled}
            for row in rows
        ]
    }


@router.get("/{comparison_id}", response_model=ComparisonDetail)
def detail(workspace_id: UUID, comparison_id: UUID, user: CurrentUser, db: Database):
    return reading.detail(db, workspace_id, user.id, comparison_id)


@router.get("/{comparison_id}/{name}/request")
def export(workspace_id: UUID, comparison_id: UUID, name: str, user: CurrentUser, db: Database):
    return reading.export(db, workspace_id, user.id, comparison_id, name)


@router.post("/{comparison_id}/{name}/response", status_code=202)
def submit(
    workspace_id: UUID,
    comparison_id: UUID,
    name: str,
    data: service.Response,
    user: CurrentUser,
    db: Database,
):
    service.submit(db, workspace_id, user.id, comparison_id, name, data)
    db.commit()
    return {"accepted": True}


@router.post("/{comparison_id}/cancel")
def cancel(workspace_id: UUID, comparison_id: UUID, user: CurrentUser, db: Database):
    service.cancel(db, workspace_id, user.id, comparison_id)
    db.commit()
    return {"cancelled": True}
