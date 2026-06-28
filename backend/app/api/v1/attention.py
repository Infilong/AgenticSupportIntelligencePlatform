from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.attention import AttentionItemResponse, AttentionSummaryResponse
from app.services.attention_service import AttentionService

router = APIRouter(prefix="/workspaces/{workspace_id}/attention", tags=["attention"])
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=AttentionSummaryResponse)
def get_attention_summary(
    workspace: WorkspaceMemberAccess, current_user: CurrentUser, db: DbSession
) -> AttentionSummaryResponse:
    summary = AttentionService(db).summarize_workspace(
        workspace_id=workspace.id, user_id=current_user.id
    )
    return AttentionSummaryResponse(
        workspace_id=str(summary.workspace_id),
        total_items=len(summary.items),
        critical_count=summary.critical_count,
        warning_count=summary.warning_count,
        info_count=summary.info_count,
        pending_reviews=summary.pending_reviews,
        assigned_to_me_reviews=summary.assigned_to_me_reviews,
        items=[
            AttentionItemResponse(
                id=item.id,
                category=item.category,
                severity=item.severity,
                title=item.title,
                detail=item.detail,
                count=item.count,
                action_label=item.action_label,
                target_tab=item.target_tab,
                target_id=item.target_id,
                created_at=item.created_at,
            )
            for item in summary.items
        ],
    )
