import json

from test_admin_hierarchy import account

from app.schemas.task_configuration import TaskConfigurationResponse


def test_configuration_whitelists_and_redacts_fields():
    result = TaskConfigurationResponse.from_snapshot(json.dumps({
        "name": "Support", "token_budget": 1000, "api_key": "private-key",
        "settings": {"instructions": "Contact customer@example.test", "secret": "hidden",
                     "knowledge_document_ids": [], "allowed_actions": ["add_note"]},
    })).model_dump(mode="json")
    assert result["instructions"] == "Contact [REDACTED]"
    assert result["knowledge_document_ids"] == []
    assert result["allowed_actions"] == ["add_note"]
    assert "private-key" not in json.dumps(result) and "hidden" not in json.dumps(result)


def test_saved_configuration_survives_agent_edit_and_is_workspace_scoped(client):
    _, _, headers = account(client, "snapshot-owner")
    _, _, foreign_headers = account(client, "snapshot-foreign")
    workspace = client.post("/api/v1/workspaces", headers=headers,
                            json={"name": "Snapshot QA"}).json()["id"]
    base = f"/api/v1/workspaces/{workspace}"
    agent = client.post(base + "/agents", headers=headers,
                        json={"name": "Original support", "token_budget": 2000}).json()["id"]
    update = client.patch(base + f"/agents/{agent}", headers=headers, json={
        "instructions": "Original instructions", "knowledge_document_ids": [],
        "allowed_actions": ["add_note"],
    })
    assert update.status_code == 200
    admitted = client.post(base + "/tasks", headers=headers, json={
        "agent_id": agent, "input_message": "Refund?", "request_key": "snapshot-test"})
    assert admitted.status_code == 202
    run_id = admitted.json()["run"]["id"]
    url = base + f"/task-runs/{run_id}/configuration"
    original = client.get(url, headers=headers)
    assert original.status_code == 200
    assert original.json()["instructions"] == "Original instructions"
    assert original.json()["name"] == "Original support"
    assert original.json()["knowledge_document_ids"] == []
    assert client.patch(base + f"/agents/{agent}", headers=headers, json={
        "name": "Changed support", "instructions": "Changed instructions",
        "knowledge_document_ids": None, "allowed_actions": [],
    }).status_code == 200
    assert client.get(url, headers=headers).json() == original.json()
    assert client.get(url).status_code == 401
    assert client.get(url, headers=foreign_headers).status_code == 404
