from sqlalchemy import func, select
from test_admin_hierarchy import account
from test_task_admission import setup

from app.models.ai import AIRun
from app.models.task import SupportTask


def test_task_api_queues_idempotently_and_stops_without_model_work(client, db_session):
    args = setup(client)
    login = client.post("/api/v1/auth/login", json={"email": "task-owner@hierarchy.test",
                                                  "password": "strong-password"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    base = f"/api/v1/workspaces/{args['workspace_id']}"
    payload = {"agent_id": str(args["agent_id"]), "input_message": "Refund?", "request_key": "api"}
    first = client.post(base + "/tasks", headers=headers, json=payload)
    assert first.status_code == 202
    result = first.json()
    assert result["run"]["status"] == "queued"
    listed = client.get(base + "/agent-runs?status=queued", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["items"][0]["id"] == result["run"]["id"]
    assert client.post(base + "/tasks", headers=headers, json=payload).json() == result
    changed = client.post(base + "/tasks", headers=headers,
                          json={**payload, "input_message": "Changed"})
    assert changed.status_code == 409
    url = base + f"/task-runs/{result['run']['id']}"
    assert client.get(url, headers=headers).json() == result
    assert client.post(url + "/stop", headers=headers).json()["status"] == "stopped"
    assert client.post(url + "/stop", headers=headers).json()["status"] == "stopped"
    assert client.get(url, headers=headers).json()["run"]["status"] == "stopped"
    assert db_session.scalar(select(func.count()).select_from(SupportTask)) == 1
    assert db_session.scalar(select(func.count()).select_from(AIRun)) == 0


def test_task_api_denies_viewer_mutation_and_foreign_read(client):
    owner, _, headers = account(client, "api-owner")
    _, viewer_email, viewer_headers = account(client, "api-viewer")
    _, _, outsider_headers = account(client, "api-outsider")
    workspace = client.post("/api/v1/workspaces", headers=headers,
                            json={"name": "Task access"}).json()["id"]
    base = f"/api/v1/workspaces/{workspace}"
    agent = client.post(base + "/agents", headers=headers, json={"name": "Support"}).json()["id"]
    assert client.post(base + "/members", headers=headers,
                       json={"email": viewer_email, "role": "viewer"}).status_code == 201
    payload = {"agent_id": agent, "input_message": "Refund?", "request_key": "access"}
    assert client.post(base + "/tasks", headers=viewer_headers, json=payload).status_code == 403
    run = client.post(base + "/tasks", headers=headers, json=payload).json()["run"]
    url = base + f"/task-runs/{run['id']}"
    assert client.get(url, headers=viewer_headers).status_code == 200
    assert client.post(url + "/stop", headers=viewer_headers).status_code == 403
    assert client.get(url, headers=outsider_headers).status_code == 404
