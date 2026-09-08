"""Read only saved artifacts belonging to a record and its selected attempt."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.api.v1.records import Db, ReadAccess
from app.schemas.record_artifact import RecordArtifactPage
from app.services.record_artifacts import list_artifacts

router = APIRouter(prefix="/workspaces/{workspace_id}/records", tags=["records"])


@router.get("/{record_id}/attempts/{run_id}/artifacts", response_model=RecordArtifactPage)
def artifacts(record_id: UUID, run_id: UUID, workspace: ReadAccess, db: Db,
              offset: int = Query(default=0, ge=0), limit: int = Query(default=20, ge=1, le=100)):
    result = list_artifacts(db, workspace_id=workspace.id, record_id=record_id,
                           run_id=run_id, offset=offset, limit=limit)
    if result is None:
        raise HTTPException(404, detail="Record attempt not found.")
    return result
