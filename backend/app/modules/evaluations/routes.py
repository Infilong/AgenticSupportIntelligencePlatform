from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import load_only

from app.modules.evaluations.models import EvaluationRecord
from app.modules.evaluations.schemas import EvaluationDetail, EvaluationList
from app.modules.identity.dependencies import CurrentUser, Database
from app.modules.workspaces.service import membership

router = APIRouter(prefix="/api/workspaces/{workspace_id}/evaluations", tags=["evaluations"])


def summary(row):
    return {key: getattr(row, key) for key in ("id", "registered_at", "report_sha256", "source_commit")}


@router.get("", response_model=EvaluationList)
def evaluations(workspace_id: UUID, user: CurrentUser, db: Database, page: int = Query(1, ge=1, le=500)):
    membership(db, workspace_id, user.id)
    rows = db.scalars(
        select(EvaluationRecord)
        .options(
            load_only(
                EvaluationRecord.id,
                EvaluationRecord.registered_at,
                EvaluationRecord.report_sha256,
                EvaluationRecord.source_commit,
            )
        )
        .where(EvaluationRecord.workspace_id == workspace_id)
        .order_by(EvaluationRecord.registered_at.desc(), EvaluationRecord.id.desc())
        .offset((page - 1) * 20)
        .limit(21)
    ).all()
    return {"items": [summary(row) for row in rows[:20]], "more": len(rows) > 20}


@router.get("/{record_id}", response_model=EvaluationDetail)
def evaluation(workspace_id: UUID, record_id: UUID, user: CurrentUser, db: Database):
    membership(db, workspace_id, user.id)
    row = db.scalar(
        select(EvaluationRecord).where(
            EvaluationRecord.workspace_id == workspace_id, EvaluationRecord.id == record_id
        )
    )
    if row is None:
        raise HTTPException(404, "Evaluation not found")
    return {**summary(row), "snapshot": row.snapshot}
