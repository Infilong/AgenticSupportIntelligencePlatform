from datetime import UTC, datetime
from uuid import UUID

from test_datasets import create_workspace, login, register

from app.models.dataset import Dataset
from app.services.dataset_service import DatasetService


def test_tied_timestamps_have_stable_nonoverlapping_pages(client, db_session):
    register(client, "pagination@example.com")
    token = login(client, "pagination@example.com")
    workspace = create_workspace(client, token)
    workspace_id = UUID(workspace["id"])
    for number in (2, 1, 3):
        db_session.add(Dataset(id=UUID(int=number), workspace_id=workspace_id,
            name=f"Dataset {number}", created_at=datetime(2026, 1, 1, tzinfo=UTC)))
    db_session.commit()
    service = DatasetService(db_session)
    first = service.list_datasets(workspace_id=workspace_id, limit=2, offset=0)
    second = service.list_datasets(workspace_id=workspace_id, limit=2, offset=2)
    assert [row.id.int for row in first] == [3, 2]
    assert [row.id.int for row in second] == [1]
