from uuid import UUID

from fastapi import APIRouter

from app.modules.identity.dependencies import CurrentUser, Database
from app.modules.reviews.schemas import ReviewInput
from app.modules.reviews.service import submit
from app.modules.support.reading import detail
from app.modules.support.schemas import RunDetail

router = APIRouter(prefix="/api/workspaces/{workspace_id}/runs", tags=["reviews"])


@router.post("/{run_id}/review", response_model=RunDetail, status_code=202)
def review(workspace_id: UUID, run_id: UUID, data: ReviewInput, user: CurrentUser, db: Database):
    submit(db, workspace_id, user.id, run_id, data)
    db.commit()
    return detail(db, workspace_id, user.id, run_id)
