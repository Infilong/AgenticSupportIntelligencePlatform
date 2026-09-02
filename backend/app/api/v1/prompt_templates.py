from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_permission
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.prompt_template import (
    PromptTemplateCreateVersionRequest,
    PromptTemplateListResponse,
    PromptTemplateResponse,
)
from app.services.audit_log_service import AuditLogService
from app.services.prompt_runtime import PromptTemplateValidationError
from app.services.prompt_template_service import (
    PromptTemplateNotFoundError,
    PromptTemplateService,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/prompt-templates", tags=["prompt-templates"])
DbSession = Annotated[Session, Depends(get_db)]
PromptReadAccess = Annotated[Workspace, Depends(require_workspace_permission("prompts:read"))]
PromptWriteAccess = Annotated[Workspace, Depends(require_workspace_permission("prompts:write"))]
CurrentUser = Annotated[User, Depends(get_current_user)]
TemplateId = Annotated[UUID, Path()]
IncludeArchived = Annotated[bool, Query()]
HistoryStatusFilter = Annotated[
    Literal["all", "active", "draft", "archived"], Query(alias="status")
]
HistorySearchFilter = Annotated[str | None, Query(max_length=160)]
HistoryLimit = Annotated[int | None, Query(ge=1, le=500)]
HistoryOffset = Annotated[int, Query(ge=0)]


@router.get("", response_model=PromptTemplateListResponse)
def list_prompt_templates(
    workspace: PromptReadAccess,
    db: DbSession,
    include_archived: IncludeArchived = False,
    status_filter: HistoryStatusFilter = "all",
    search: HistorySearchFilter = None,
    limit: HistoryLimit = None,
    offset: HistoryOffset = 0,
) -> PromptTemplateListResponse:
    service = PromptTemplateService(db)
    templates = service.list_templates(
        workspace_id=workspace.id,
        include_archived=include_archived,
        status_filter=status_filter,
        search=search,
        limit=limit,
        offset=offset,
    )
    total = service.count_templates(
        workspace_id=workspace.id,
        include_archived=include_archived,
        status_filter=status_filter,
        search=search,
    )
    return PromptTemplateListResponse(
        items=[PromptTemplateResponse.model_validate(template) for template in templates],
        total=total,
        limit=limit,
        offset=offset,
        has_next=offset + len(templates) < total,
    )


@router.post("", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_prompt_template_version(
    payload: PromptTemplateCreateVersionRequest,
    workspace: PromptWriteAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> PromptTemplateResponse:
    try:
        template = PromptTemplateService(db).create_version(
            workspace_id=workspace.id,
            name=payload.name,
            language=payload.language,
            template_text=payload.template_text,
            active=payload.active,
        )
    except PromptTemplateValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "prompt_template_invalid", "message": str(exc)},
        ) from exc
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
    workspace: PromptWriteAccess,
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
    except PromptTemplateValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "prompt_template_invalid", "message": str(exc)},
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


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_prompt_template(
    template_id: TemplateId,
    workspace: PromptWriteAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    try:
        template = PromptTemplateService(db).archive(
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
        action="prompt_template.archived",
        resource_type="prompt_template",
        resource_id=template.id,
        metadata={
            "name": template.name,
            "language": template.language,
            "version": template.version,
            "archived_at": template.archived_at.isoformat() if template.archived_at else None,
        },
    )
