from test_admin_hierarchy import account
from test_task_admission import setup

from app.services.task_admission import admit_task


def test_retry_api_is_scoped_idempotent_and_history_is_bounded(client, db_session):
    args = setup(client)
    task, parent = admit_task(db_session, **args)
    parent.status = "stopped"
    db_session.commit()
    login = client.post("/api/v1/auth/login", json={"email": "task-owner@hierarchy.test",
                                                   "password": "strong-password"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    base = f"/api/v1/workspaces/{parent.workspace_id}"
    url = base + f"/task-runs/{parent.id}/retry"
    body = {"request_key": "retry", "corrected_instructions": "Explain receipt rules"}
    _, email, viewer = account(client, "retry-viewer")
    client.post(base + "/members", headers=headers, json={"email": email, "role": "viewer"})
    assert client.post(url, headers=viewer, json=body).status_code == 403
    first = client.post(url, headers=headers, json=body)
    assert first.status_code == 202
    result = first.json()
    assert result["parent_run_id"] == str(parent.id)
    assert result["task_id"] == str(task.id)
    assert result["run"]["status"] == "queued"
    assert client.post(url, headers=headers, json=body).json() == result
    assert client.post(url, headers=headers, json={**body,
        "corrected_instructions": "Changed"}).status_code == 409
    child = result["run"]["id"]
    assert client.get(base + f"/task-runs/{child}", headers=headers).json() == result
    history = client.get(base + f"/task-runs/{child}/attempts?limit=1", headers=viewer).json()
    assert history["total"] == 2 and history["has_next"]
    assert history["items"][0]["run"]["id"] == child
    older = client.get(base + f"/task-runs/{child}/attempts?limit=1&offset=1",
                       headers=viewer).json()
    assert older["items"][0]["run"]["id"] == str(parent.id)
    foreign = client.post("/api/v1/workspaces", headers=headers,
                          json={"name": "Other"}).json()["id"]
    foreign_base = f"/api/v1/workspaces/{foreign}/task-runs/{parent.id}"
    assert client.post(foreign_base + "/retry", headers=headers, json=body).status_code == 404
    assert client.get(foreign_base + "/attempts", headers=headers).status_code == 404
    assert client.post(url, headers=headers, json={**body,
        "corrected_instructions": "  "}).status_code == 422
