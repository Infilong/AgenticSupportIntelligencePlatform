"""Original data is durable before model work and remains unchanged across retries."""

from uuid import UUID

import pytest
from sqlalchemy import func, select
from test_admin_hierarchy import account
from test_records_api import fixture_records

from app.models.agent import GraphRun
from app.models.ai import AIRun
from app.models.task import SupportTask
from app.services.task_admission import admit_task


@pytest.mark.parametrize("original", [
    {"format": "text", "content": "  返金について教えてください。\n", "source": "admin"},
    {"format": "json", "content": {"question": "Refund policy?", "order": {"days": 3}},
     "source": "api", "source_reference": "order-42"},
])
def test_original_input_saved_before_execution_and_preserved_on_retry(client, db_session, original):
    base, agent, headers = fixture_records(client)
    payload = {"agent_id": agent, "request_key": "original", "input": original}
    response = client.post(base + "/records", headers=headers, json=payload)
    assert response.status_code == 202, response.text
    record = response.json()
    assert record["input"]["content"] == original["content"]
    assert record["input"]["source"] == original["source"]
    assert record["status"] == "queued"
    assert db_session.scalar(select(func.count()).select_from(AIRun)) == 0
    assert client.post(base + "/records", headers=headers, json=payload).json() == record
    changed = {**payload, "input": {**original, "source_reference": "different"}}
    assert client.post(base + "/records", headers=headers, json=changed).status_code == 409
    parent = db_session.get(GraphRun, UUID(record["latest_run_id"]))
    parent.status = "stopped"
    db_session.commit()
    _, child = admit_task(db_session, workspace_id=parent.workspace_id,
        user_id=parent.user_id, agent_id=parent.agent_config_id, message=parent.input_message,
        request_key="retry", parent_run_id=parent.id, corrected_instructions="Check evidence")
    detail = client.get(base + "/records/" + record["id"], headers=headers).json()
    assert detail["input"] == record["input"]
    assert detail["latest_run_id"] == str(child.id)
    assert detail["attempt_count"] == 2
    assert db_session.scalar(select(func.count()).select_from(SupportTask)) == 1


@pytest.mark.parametrize("original", [
    {"format": "text", "content": "   "},
    {"format": "text", "content": {"a": 1}},
    {"format": "json", "content": "not an object"},
    {"format": "json", "content": {}},
    {"format": "text", "content": "x" * 12001},
    {"content": "Hello", "created_by_user_id": "forged"},
], ids=["blank", "text-type", "json-type", "empty-json", "oversize", "forged-identity"])
def test_invalid_record_input_does_not_persist(client, db_session, original):
    base, agent, headers = fixture_records(client)
    result = client.post(base + "/records", headers=headers,
        json={"agent_id": agent, "request_key": "invalid", "input": original})
    assert result.status_code == 422
    assert db_session.scalar(select(func.count()).select_from(SupportTask)) == 0


def test_record_intake_denies_viewer_and_foreign_agent(client, db_session):
    base, agent, headers = fixture_records(client)
    _, email, viewer = account(client, "record-submit-viewer")
    client.post(base + "/members", headers=headers, json={"email": email, "role": "viewer"})
    payload = {"agent_id": agent, "request_key": "denied", "input": {"content": "Question"}}
    assert client.post(base + "/records", headers=viewer, json=payload).status_code == 403
    second = client.post("/api/v1/workspaces", headers=headers,
                         json={"name": "Other"}).json()["id"]
    result = client.post(f"/api/v1/workspaces/{second}/records", headers=headers, json=payload)
    assert result.status_code == 409
    assert db_session.scalar(select(func.count()).select_from(SupportTask)) == 0
