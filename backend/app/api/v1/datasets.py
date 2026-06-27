from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.dataset import (
    ConversationExampleResponse,
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

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["datasets"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]
DatasetId = Annotated[UUID, Path()]
ExampleId = Annotated[UUID, Path()]


@router.post(
    "/datasets/import",
    response_model=DatasetImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_dataset(
    payload: DatasetImportRequest,
    workspace: WorkspaceMemberAccess,
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
        )
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
def list_datasets(workspace: WorkspaceMemberAccess, db: DbSession) -> list[DatasetResponse]:
    datasets = DatasetService(db).list_datasets(workspace_id=workspace.id)
    return [DatasetResponse.model_validate(dataset) for dataset in datasets]


@router.get("/datasets/{dataset_id}/examples", response_model=list[ConversationExampleResponse])
def list_examples(
    dataset_id: DatasetId,
    workspace: WorkspaceMemberAccess,
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
    workspace: WorkspaceMemberAccess,
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
