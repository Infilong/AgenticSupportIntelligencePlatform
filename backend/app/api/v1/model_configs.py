from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.workspace import require_workspace_member
from app.models.workspace import Workspace
from app.schemas.model_config import ModelConfigCreateRequest, ModelConfigResponse
from app.services.model_config_service import ModelConfigNotFoundError, ModelConfigService

router = APIRouter(prefix="/workspaces/{workspace_id}/model-configs", tags=["model-configs"])
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]
ModelConfigId = Annotated[UUID, Path()]


@router.get("", response_model=list[ModelConfigResponse])
def list_model_configs(
    workspace: WorkspaceMemberAccess, db: DbSession
) -> list[ModelConfigResponse]:
    configs = ModelConfigService(db).list_configs(workspace_id=workspace.id)
    return [ModelConfigResponse.model_validate(config) for config in configs]


@router.post("", response_model=ModelConfigResponse, status_code=status.HTTP_201_CREATED)
def create_model_config(
    payload: ModelConfigCreateRequest,
    workspace: WorkspaceMemberAccess,
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
    return ModelConfigResponse.model_validate(config)


@router.post("/{model_config_id}/activate", response_model=ModelConfigResponse)
def activate_model_config(
    model_config_id: ModelConfigId,
    workspace: WorkspaceMemberAccess,
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
    return ModelConfigResponse.model_validate(config)
