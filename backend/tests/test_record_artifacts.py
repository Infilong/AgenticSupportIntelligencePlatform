"""Saved artifacts retain evidence but omit private state and foreign attempts."""

import json
from uuid import uuid4

from test_record_clarifications import waiting

from app.models.agent import GraphStep


def test_artifacts_read_saved_output_and_report_corruption(client, db_session):
    base, headers, record, run = waiting(client, db_session)
    step = GraphStep(workspace_id=run.workspace_id, graph_run_id=run.id,
        step_name="compress_context", input_json="{}", output_json=json.dumps({
            "packed_context_chunks": [{"content": "Contact private@example.com",
                "document_id": str(uuid4()), "version": 2, "system_prompt": "private"}],
            "chain_of_thought": "private"}), status="succeeded", latency_ms=1, sequence=2)
    db_session.add(step)
    db_session.commit()
    url = base + f"/records/{record['id']}/attempts/{run.id}/artifacts"
    response = client.get(url, headers=headers)
    assert response.status_code == 200
    page = response.json()
    assert page["total"] == 2
    assert page["items"][0]["kind"] == "request_clarification"
    evidence = page["items"][1]["data"]["packed_context_chunks"][0]
    assert evidence["version"] == 2
    assert "system_prompt" not in evidence
    assert "private@example.com" not in response.text
    assert "chain_of_thought" not in response.text
    assert "private@example.com" in step.output_json
    limited = client.get(url + "?limit=1", headers=headers).json()
    assert limited["has_next"] and len(limited["items"]) == 1
    step.output_json = "corrupt"
    db_session.commit()
    broken = client.get(url + "?offset=1", headers=headers).json()["items"][0]
    assert broken["error"] == "Saved artifact cannot be decoded."


def test_artifacts_require_matching_record_workspace_and_access(client, db_session):
    base, headers, record, run = waiting(client, db_session)
    url = base + f"/records/{record['id']}/attempts/{run.id}/artifacts"
    assert client.get(url).status_code == 401
    assert client.get(url.replace(record["id"], str(uuid4())), headers=headers).status_code == 404
    second = client.post("/api/v1/workspaces", headers=headers, json={"name": "Other"}).json()["id"]
    foreign = url.replace(str(run.workspace_id), second)
    assert client.get(foreign, headers=headers).status_code == 404
    assert client.get(url + "?limit=101", headers=headers).status_code == 422
