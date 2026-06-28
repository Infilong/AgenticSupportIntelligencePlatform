from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_permission
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.model_config import ModelConfigCreateRequest, ModelConfigResponse
from app.services.audit_log_service import AuditLogService
from app.services.model_config_service import ModelConfigNotFoundError, ModelConfigService

router = APIRouter(prefix="/workspaces/{workspace_id}/model-configs", tags=["model-configs"])
DbSession = Annotated[Session, Depends(get_db)]
ModelReadAccess = Annotated[Workspace, Depends(require_workspace_permission("models:read"))]
ModelWriteAccess = Annotated[Workspace, Depends(require_workspace_permission("models:write"))]
CurrentUser = Annotated[User, Depends(get_current_user)]
ModelConfigId = Annotated[UUID, Path()]
IncludeArchived = Annotated[bool, Query()]


@router.get("", response_model=list[ModelConfigResponse])
def list_model_configs(
    workspace: ModelReadAccess,
    db: DbSession,
    include_archived: IncludeArchived = False,
) -> list[ModelConfigResponse]:
    configs = ModelConfigService(db).list_configs(
        workspace_id=workspace.id, include_archived=include_archived
    )
    return [ModelConfigResponse.model_validate(config) for config in configs]


@router.post("", response_model=ModelConfigResponse, status_code=status.HTTP_201_CREATED)
def create_model_config(
    payload: ModelConfigCreateRequest,
    workspace: ModelWriteAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> ModelConfigResponse:
    config = ModelConfigService(db).create_config(
        workspace_id=workspace.id,
        provider=payload.provider,
        model=payload.model,
        purpose=payload.purpose,
        prompt_token_cost_per_1k=payload.prompt_token_cost_per_1k,
        completion_token_cost_per_1k=payload.completion_token_cost_per_1k,
        max_context_tokens=payload.max_context_tokens,
        active=payload.active,
    )
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="model_config.created",
        resource_type="model_config",
        resource_id=config.id,
        metadata={
            "provider": config.provider,
            "model": config.model,
            "purpose": config.purpose,
            "active": config.active,
        },
    )
    return ModelConfigResponse.model_validate(config)


@router.post("/{model_config_id}/activate", response_model=ModelConfigResponse)
def activate_model_config(
    model_config_id: ModelConfigId,
    workspace: ModelWriteAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> ModelConfigResponse:
    try:
        config = ModelConfigService(db).activate(
            workspace_id=workspace.id, model_config_id=model_config_id
        )
    except ModelConfigNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "model_config_not_found",
                "message": "Model config was not found.",
            },
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="model_config.activated",
        resource_type="model_config",
        resource_id=config.id,
        metadata={"provider": config.provider, "model": config.model, "purpose": config.purpose},
    )
    return ModelConfigResponse.model_validate(config)


@router.delete("/{model_config_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_model_config(
    model_config_id: ModelConfigId,
    workspace: ModelWriteAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    try:
        config = ModelConfigService(db).archive(
            workspace_id=workspace.id, model_config_id=model_config_id
        )
    except ModelConfigNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "model_config_not_found",
                "message": "Model config was not found.",
            },
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="model_config.archived",
        resource_type="model_config",
        resource_id=config.id,
        metadata={
            "provider": config.provider,
            "model": config.model,
            "purpose": config.purpose,
            "archived_at": config.archived_at.isoformat() if config.archived_at else None,
        },
    )
