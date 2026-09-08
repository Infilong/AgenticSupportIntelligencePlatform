"""Failed language validation must not publish a usable prefix of an import."""

import json

import pytest
from sqlalchemy import select
from test_datasets import auth_headers, create_workspace, login, register

from app.models.dataset import ConversationExample, ImportBatch, ImportStatus, Label, Message


@pytest.mark.parametrize("case", ["csv", "jsonl", "message"])
def test_late_language_failure_keeps_batch_without_partial_examples(client, db_session, case):
    register(client, "import-failure@example.test")
    token = login(client, "import-failure@example.test")
    headers = auth_headers(token)
    workspace = create_workspace(client, token)
    base = f"/api/v1/workspaces/{workspace['id']}/datasets"
    valid = {"messages": [{"role": "user", "content": "Can I get a refund?"}],
             "labels": {"intent": "refund_request"}}
    initial = client.post(base + "/import", headers=headers, json={
        "dataset_name": "Existing", "source_type": "jsonl", "content": json.dumps(valid),
    })
    assert initial.status_code == 201

    def snapshot():
        return [db_session.execute(select(*model.__table__.c).order_by(model.id)).all()
                for model in (ConversationExample, Message, Label)]

    before = snapshot()
    if case == "csv":
        source = "csv"
        content = ("role,content,label_intent\n"
                   "user,Can I get a refund?,refund_request\nuser,12345,\n")
    else:
        source = "jsonl"
        invalid = {"messages": [{"role": "user", "content": "12345"}]}
        if case == "message":
            invalid["messages"][0]["content"] = "Привет"
            invalid["messages"].insert(0, {"role": "user", "content": "Another refund request"})
        content = "\n".join(json.dumps(row) for row in (valid, invalid))
    failed = client.post(base + "/import", headers=headers, json={
        "dataset_name": "Rejected", "source_type": source, "content": content,
    })
    assert failed.status_code == 400
    assert failed.json()["detail"]["code"] == "dataset_import_failed"
    assert snapshot() == before
    batch, = db_session.scalars(select(ImportBatch).where(
        ImportBatch.status == ImportStatus.failed,
    )).all()
    assert batch.error_message
    listed = client.get(f"{base}/{batch.dataset_id}/examples", headers=headers)
    assert listed.status_code == 200
    assert listed.json() == []
    retry = client.post(base + "/import", headers=headers, json={
        "dataset_name": "Corrected", "source_type": "jsonl", "content": json.dumps(valid),
    })
    assert retry.status_code == 201
    assert retry.json()["imported_examples"] == 1
