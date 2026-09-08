import json

import pytest
from sqlalchemy import select

from app.models.dataset import ConversationExample, ImportBatch, ImportStatus, Message
from tests.test_datasets import auth_headers, create_workspace, login, register


@pytest.mark.parametrize("content", [{"private": "refund"}, ["private refund"], 123, True])
def test_jsonl_rejects_nontext_messages_without_partial_examples(client, db_session, content):
    register(client, "jsonl-types@example.test")
    token = login(client, "jsonl-types@example.test")
    workspace = create_workspace(client, token)
    headers = auth_headers(token)
    base = f"/api/v1/workspaces/{workspace['id']}/datasets"
    valid = {"language": "en", "messages": [{"role": "user", "content": "Refund request"}]}
    invalid = {"language": "en", "messages": [{"role": "user", "content": content}]}
    response = client.post(base + "/import", headers=headers, json={
        "dataset_name": "Invalid message type", "source_type": "jsonl",
        "content": "\n".join(json.dumps(row) for row in (valid, invalid)),
    })
    assert response.status_code == 400, response.text
    assert response.json()["detail"]["code"] == "dataset_import_failed"
    assert "must be a string" in response.json()["detail"]["message"]
    assert "private" not in response.text
    assert db_session.scalar(select(ConversationExample)) is None
    assert db_session.scalar(select(Message)) is None
    batch, = db_session.scalars(select(ImportBatch)).all()
    assert batch.status == ImportStatus.failed
    assert client.get(f"{base}/{batch.dataset_id}/examples", headers=headers).json() == []

    # Numeric text is legitimate conversation content when language is declared.
    valid["messages"][0]["content"] = "123"
    repaired = client.post(base + "/import", headers=headers, json={
        "dataset_name": "Corrected message type", "source_type": "jsonl",
        "content": json.dumps(valid),
    })
    assert repaired.status_code == 201
    path = f"{base}/{repaired.json()['dataset']['id']}/examples"
    examples = client.get(path, headers=headers)
    assert examples.status_code == 200
    assert examples.json()[0]["messages"][0]["content"] == "123"
