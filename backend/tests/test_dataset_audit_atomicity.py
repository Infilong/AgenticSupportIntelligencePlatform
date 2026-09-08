import json
import os

import pytest
from sqlalchemy import event, select
from sqlalchemy.orm import Session
from test_datasets import auth_headers, create_workspace, login, register
from test_resource_folders import create_folder
from test_review_transactions import review_database as review_database

from app.models.audit import AuditLog
from app.models.dataset import (
    ConversationExample,
    Dataset,
    ImportBatch,
    ImportSourceType,
    Label,
    Message,
)
from app.models.folder import ResourceFolder
from app.services.dataset_service import DatasetService

CONTENT = json.dumps({"messages": [{"role": "user", "content": "Can I get a refund?"}],
                      "labels": {"intent": "refund_request"}})


def snapshot(db):
    db.expire_all()
    return [db.execute(select(*model.__table__.c).order_by(model.id)).all()
            for model in (Dataset, ImportBatch, ConversationExample, Message, Label, AuditLog)]


def reject_audit(db, context, instances):
    if any(isinstance(row, AuditLog) for row in db.new):
        raise RuntimeError("synthetic dataset audit failure")


@pytest.mark.parametrize("operation", ["move", "delete"])
def test_dataset_audit_failure_rolls_back_children(client, db_session, operation):
    register(client, "dataset-atomic@example.test")
    token = login(client, "dataset-atomic@example.test")
    headers = auth_headers(token)
    workspace = create_workspace(client, token)
    folder = create_folder(client, token, workspace["id"], "dataset", "Destination")
    base = f"/api/v1/workspaces/{workspace['id']}/datasets"
    imported = client.post(base + "/import", headers=headers, json={
        "dataset_name": "Original", "source_type": "jsonl", "content": CONTENT,
    })
    assert imported.status_code == 201
    path = base + "/" + imported.json()["dataset"]["id"]
    method, body, status = "DELETE", None, 204
    if operation == "move":
        method, path, body, status = "PATCH", path + "/folder", {"folder_id": folder["id"]}, 200
    before = snapshot(db_session)
    assert all(before[index] for index in range(5))
    event.listen(db_session, "before_flush", reject_audit)
    try:
        with pytest.raises(RuntimeError, match="synthetic dataset audit failure"):
            client.request(method, path, headers=headers, json=body)
    finally:
        event.remove(db_session, "before_flush", reject_audit)
        db_session.rollback()
    assert snapshot(db_session) == before
    assert client.request(method, path, headers=headers, json=body).status_code == status
    assert len(snapshot(db_session)[-1]) == len(before[-1]) + 1


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
@pytest.mark.parametrize("operation", ["move", "delete"])
def test_postgres_dataset_audit_is_atomic(review_database, operation):
    engine, ids = review_database
    with Session(engine) as db:
        folder = ResourceFolder(workspace_id=ids[0], created_by_user_id=ids[2][0],
                                resource_type="dataset", name="Destination")
        db.add(folder)
        db.commit()
        folder_id = folder.id
        result = DatasetService(db).import_dataset(
            workspace_id=ids[0], dataset_name="Original", description=None,
            source_type=ImportSourceType.jsonl, content=CONTENT,
        )
        dataset_id = result.dataset.id

    def observe():
        with Session(engine) as observer:
            return snapshot(observer)

    before = observe()
    observed = []

    def fail(db, context, instances):
        if any(isinstance(row, AuditLog) for row in db.new):
            observed.append(observe())
            reject_audit(db, context, instances)

    with Session(engine) as db:
        service = DatasetService(db)

        def mutate():
            args = {"workspace_id": ids[0], "dataset_id": dataset_id,
                    "actor_user_id": ids[2][0]}
            if operation == "move":
                return service.move_dataset(**args, folder_id=folder_id)
            return service.delete_dataset(**args)

        event.listen(db, "before_flush", fail)
        try:
            with pytest.raises(RuntimeError, match="synthetic dataset audit failure"):
                mutate()
        finally:
            event.remove(db, "before_flush", fail)
        assert observed == [before]
        assert observe() == before
        assert db.is_active
        mutate()
    after = observe()
    assert after[0] != before[0]
    audit, = after[-1]
    assert audit.actor_user_id == ids[2][0]
