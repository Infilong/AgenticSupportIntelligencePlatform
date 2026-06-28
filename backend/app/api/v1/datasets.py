from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_permission
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.dataset import (
    ConversationExampleResponse,
    DatasetFolderUpdateRequest,
    DatasetImportRequest,
    DatasetImportResponse,
    DatasetResponse,
    LabelEditRequest,
    LabelResponse,
)
from app.services.dataset_service import (
    DatasetImportError,
    DatasetNotFoundError,
    DatasetService,
    ExampleNotFoundError,
)
from app.services.folder_service import ResourceFolderNotFoundError

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["datasets"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
DatasetReadAccess = Annotated[Workspace, Depends(require_workspace_permission("data:read"))]
DatasetWriteAccess = Annotated[
    Workspace, Depends(require_workspace_permission("data:write"))
]
ResourceFolderManageAccess = Annotated[
    Workspace, Depends(require_workspace_permission("resource_folders:manage"))
]
ResourceDeleteAccess = Annotated[
    Workspace, Depends(require_workspace_permission("resources:delete"))
]
FolderFilter = Annotated[UUID | None, Query()]
DatasetId = Annotated[UUID, Path()]
ExampleId = Annotated[UUID, Path()]


@router.post(
    "/datasets/import",
    response_model=DatasetImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_dataset(
    payload: DatasetImportRequest,
    workspace: DatasetWriteAccess,
    db: DbSession,
) -> DatasetImportResponse:
    service = DatasetService(db)
    try:
        result = service.import_dataset(
            workspace_id=workspace.id,
            dataset_name=payload.dataset_name,
            description=payload.description,
            source_type=payload.source_type,
            content=payload.content,
            folder_id=payload.folder_id,
        )
    except ResourceFolderNotFoundError as exc:
        raise _folder_not_found(exc) from exc
    except DatasetImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "dataset_import_failed", "message": str(exc)},
        ) from exc

    return DatasetImportResponse(
        dataset=DatasetResponse.model_validate(result.dataset),
        import_batch=result.import_batch,
        imported_examples=result.imported_examples,
    )


@router.get("/datasets", response_model=list[DatasetResponse])
def list_datasets(
    workspace: DatasetReadAccess,
    db: DbSession,
    folder_id: FolderFilter = None,
) -> list[DatasetResponse]:
    try:
        datasets = DatasetService(db).list_datasets(workspace_id=workspace.id, folder_id=folder_id)
    except ResourceFolderNotFoundError as exc:
        raise _folder_not_found(exc) from exc
    return [DatasetResponse.model_validate(dataset) for dataset in datasets]


@router.get("/datasets/{dataset_id}/examples", response_model=list[ConversationExampleResponse])
def list_examples(
    dataset_id: DatasetId,
    workspace: DatasetReadAccess,
    db: DbSession,
) -> list[ConversationExampleResponse]:
    try:
        examples = DatasetService(db).list_examples(
            workspace_id=workspace.id, dataset_id=dataset_id
        )
    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "dataset_not_found", "message": "Dataset was not found."},
        ) from exc
    return [ConversationExampleResponse.model_validate(example) for example in examples]


@router.post("/examples/{example_id}/labels", response_model=LabelResponse)
def edit_label(
    example_id: ExampleId,
    payload: LabelEditRequest,
    workspace: DatasetWriteAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> LabelResponse:
    try:
        label = DatasetService(db).upsert_human_label(
            workspace_id=workspace.id,
            example_id=example_id,
            label_type=payload.label_type,
            value=payload.value,
            current_user=current_user,
        )
    except ExampleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "example_not_found", "message": "Example was not found."},
        ) from exc
    return LabelResponse.model_validate(label)


@router.patch("/datasets/{dataset_id}/folder", response_model=DatasetResponse)
def move_dataset_folder(
    dataset_id: DatasetId,
    payload: DatasetFolderUpdateRequest,
    workspace: ResourceFolderManageAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> DatasetResponse:
    try:
        dataset = DatasetService(db).move_dataset(
            workspace_id=workspace.id,
            dataset_id=dataset_id,
            folder_id=payload.folder_id,
        )
    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "dataset_not_found", "message": "Dataset was not found."},
        ) from exc
    except ResourceFolderNotFoundError as exc:
        raise _folder_not_found(exc) from exc
    return _dataset_changed_response(
        db=db,
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="dataset.moved",
        dataset=dataset,
    )


@router.delete("/datasets/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: DatasetId,
    workspace: ResourceDeleteAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    try:
        DatasetService(db).delete_dataset(workspace_id=workspace.id, dataset_id=dataset_id)
    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "dataset_not_found", "message": "Dataset was not found."},
        ) from exc
    from app.services.audit_log_service import AuditLogService

    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="dataset.deleted",
        resource_type="dataset",
        resource_id=dataset_id,
    )


def _folder_not_found(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "resource_folder_not_found", "message": "Resource folder was not found."},
    )


def _dataset_changed_response(
    *, db: DbSession, workspace_id, actor_user_id, action: str, dataset
) -> DatasetResponse:
    from app.services.audit_log_service import AuditLogService

    AuditLogService(db).record(
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        action=action,
        resource_type="dataset",
        resource_id=dataset.id,
        metadata={
            "name": dataset.name,
            "folder_id": str(dataset.folder_id) if dataset.folder_id else None,
        },
    )
    return DatasetResponse.model_validate(dataset)
