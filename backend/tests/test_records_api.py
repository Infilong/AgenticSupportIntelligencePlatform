"""Record identity, latest-attempt filtering and denied workspace access."""

from test_admin_hierarchy import account

from app.services.task_admission import admit_task


def fixture_records(client):
    _, _, headers = account(client, "records-owner")
    workspace = client.post("/api/v1/workspaces", headers=headers,
                            json={"name": "Records"}).json()["id"]
    base = f"/api/v1/workspaces/{workspace}"
    agent = client.post(base + "/agents", headers=headers,
                        json={"name": "Processor"}).json()["id"]
    return base, agent, headers


def submit(client, base, agent, headers, message, key):
    response = client.post(base + "/tasks", headers=headers, json={
        "agent_id": agent, "input_message": message, "request_key": key})
    assert response.status_code == 202
    return response.json()


def test_records_group_retries_and_filter_latest_status(client, db_session):
    from uuid import UUID

    from app.models.agent import GraphRun

    base, agent, headers = fixture_records(client)
    original = submit(client, base, agent, headers, "Original policy question", "first")
    parent = db_session.get(GraphRun, UUID(original["run"]["id"]))
    parent.status = "stopped"
    db_session.commit()
    _, child = admit_task(db_session, workspace_id=parent.workspace_id,
        user_id=parent.user_id, agent_id=parent.agent_config_id, message=parent.input_message,
        request_key="retry", parent_run_id=parent.id, corrected_instructions="Use current policy")
    child.status = "completed"
    child.final_answer = "Answer " * 100
    db_session.commit()
    page = client.get(base + "/records", headers=headers).json()
    assert page["total"] == 1
    record = page["items"][0]
    assert record["id"] == original["task_id"]
    assert record["input_message"] == "Original policy question"
    assert record["attempt_count"] == 2
    assert record["latest_run_id"] == str(child.id)
    assert record["status"] == "completed"
    assert len(record["result_summary"]) == 240
    assert client.get(base + "/records?status=stopped", headers=headers).json()["total"] == 0
    detail = client.get(base + "/records/" + record["id"], headers=headers).json()
    assert {key: detail[key] for key in record} == record
    assert detail["input"]["source"] == "unknown"
    assert detail["input"]["content"] == record["input_message"]


def test_records_pagination_literal_search_and_validation(client):
    base, agent, headers = fixture_records(client)
    submit(client, base, agent, headers, "Discount 10%", "one")
    submit(client, base, agent, headers, "Other question", "two")
    page = client.get(base + "/records?limit=1", headers=headers).json()
    assert page["total"] == 2 and page["has_next"]
    other = client.get(base + "/records?limit=1&offset=1", headers=headers).json()
    assert not other["has_next"]
    assert other["items"][0]["id"] != page["items"][0]["id"]
    literal = client.get(base + "/records", headers=headers, params={"search": "%"}).json()
    assert literal["total"] == 1
    assert literal["items"][0]["input_message"] == "Discount 10%"
    for query in ("limit=101", "limit=0", "offset=-1", "status=invalid"):
        assert client.get(base + "/records?" + query, headers=headers).status_code == 422


def test_records_permission_and_foreign_identifier_denial(client):
    base, agent, headers = fixture_records(client)
    result = submit(client, base, agent, headers, "Private input", "private")
    _, email, viewer = account(client, "records-viewer")
    _, _, outsider = account(client, "records-outsider")
    assert client.post(base + "/members", headers=headers,
                       json={"email": email, "role": "viewer"}).status_code == 201
    detail = base + "/records/" + result["task_id"]
    assert client.get(detail, headers=viewer).status_code == 200
    assert client.get(detail, headers=outsider).status_code == 404
    assert client.get(base + "/records", headers=outsider).status_code == 404
    assert client.get(base + "/records").status_code == 401
    second = client.post("/api/v1/workspaces", headers=headers,
                         json={"name": "Other workspace"}).json()["id"]
    foreign = f"/api/v1/workspaces/{second}/records"
    assert client.get(foreign, headers=headers).json()["total"] == 0
    assert client.get(foreign + "/" + result["task_id"], headers=headers).status_code == 404
