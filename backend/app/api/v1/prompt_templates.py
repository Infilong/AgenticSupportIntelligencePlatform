from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.prompt_template import (
    PromptTemplateCreateVersionRequest,
    PromptTemplateResponse,
)
from app.services.audit_log_service import AuditLogService
from app.services.prompt_template_service import (
    PromptTemplateNotFoundError,
    PromptTemplateService,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/prompt-templates", tags=["prompt-templates"])
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]
CurrentUser = Annotated[User, Depends(get_current_user)]
TemplateId = Annotated[UUID, Path()]


@router.get("", response_model=list[PromptTemplateResponse])
def list_prompt_templates(
    workspace: WorkspaceMemberAccess, db: DbSession
) -> list[PromptTemplateResponse]:
    templates = PromptTemplateService(db).list_templates(workspace_id=workspace.id)
    return [PromptTemplateResponse.model_validate(template) for template in templates]


@router.post("", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_prompt_template_version(
    payload: PromptTemplateCreateVersionRequest,
    workspace: WorkspaceMemberAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> PromptTemplateResponse:
    template = PromptTemplateService(db).create_version(
        workspace_id=workspace.id,
        name=payload.name,
        language=payload.language,
        template_text=payload.template_text,
        active=payload.active,
    )
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="prompt_template.version_created",
        resource_type="prompt_template",
        resource_id=template.id,
        metadata={
            "name": template.name,
            "language": template.language,
            "version": template.version,
        },
    )
    return PromptTemplateResponse.model_validate(template)


@router.post("/{template_id}/activate", response_model=PromptTemplateResponse)
def activate_prompt_template(
    template_id: TemplateId,
    workspace: WorkspaceMemberAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> PromptTemplateResponse:
    try:
        template = PromptTemplateService(db).activate(
            workspace_id=workspace.id, template_id=template_id
        )
    except PromptTemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "prompt_template_not_found",
                "message": "Prompt template was not found.",
            },
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="prompt_template.activated",
        resource_type="prompt_template",
        resource_id=template.id,
        metadata={
            "name": template.name,
            "language": template.language,
            "version": template.version,
        },
    )
    return PromptTemplateResponse.model_validate(template)
