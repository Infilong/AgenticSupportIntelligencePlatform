from sqlalchemy import func, select
from test_admin_hierarchy import account
from test_task_actions import pending

from app.models.agent import ToolCall
from app.models.review import HumanReview
from app.models.task_action import TaskNote


def test_action_api_binds_inputs_and_blocks_answer_bypass(client, db_session):
    _, run, proposal, _ = pending(client, db_session)
    login = client.post("/api/v1/auth/login", json={"email": "task-owner@hierarchy.test",
                                                   "password": "strong-password"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    base = f"/api/v1/workspaces/{run.workspace_id}"
    review = HumanReview(workspace_id=run.workspace_id, graph_run_id=run.id,
        reason="task_action_approval", proposed_answer="Safe answer", reviewer_decision="pending")
    db_session.add(review)
    db_session.commit()
    answer_url = base + f"/human-reviews/{review.id}/resolve"
    denied = client.post(answer_url, headers=headers, json={"decision": "approved"})
    assert denied.status_code == 400
    assert "task actions" in denied.text
    actions_url = base + f"/task-runs/{run.id}/actions"
    listed = client.get(actions_url, headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["inputs"] == {"action": "add_note", "value": "返金確認"}
    url = base + f"/task-actions/{proposal.id}/resolve"
    assert client.post(url, headers=headers, json={"expected_hash": "a" * 64,
                                                  "decision": "approve"}).status_code == 409
    _, email, viewer_headers = account(client, "action-viewer")
    assert client.post(base + "/members", headers=headers,
                       json={"email": email, "role": "viewer"}).status_code == 201
    assert client.get(actions_url, headers=viewer_headers).status_code == 200
    body = {"expected_hash": proposal.proposal_hash, "decision": "approve"}
    assert client.post(url, headers=viewer_headers, json=body).status_code == 403
    foreign = client.post("/api/v1/workspaces", headers=headers,
                          json={"name": "Other"}).json()["id"]
    assert client.get(f"/api/v1/workspaces/{foreign}/task-runs/{run.id}/actions",
                      headers=headers).status_code == 404
    for _ in range(2):
        resolved = client.post(url, headers=headers, json=body)
        assert resolved.status_code == 200
        assert resolved.json()["status"] == "applied"
    assert db_session.scalar(select(func.count()).select_from(TaskNote)) == 1
    assert db_session.scalar(select(func.count()).select_from(ToolCall).where(
        ToolCall.tool_name == "add_note")) == 1
    published = client.post(answer_url, headers=headers, json={"decision": "approved"})
    assert published.status_code == 200


def test_rejecting_answer_rejects_pending_actions(client, db_session):
    _, run, proposal, _ = pending(client, db_session)
    login = client.post("/api/v1/auth/login", json={"email": "task-owner@hierarchy.test",
                                                   "password": "strong-password"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    review = HumanReview(workspace_id=run.workspace_id, graph_run_id=run.id,
        reason="task_action_approval", proposed_answer="Safe answer", reviewer_decision="pending")
    db_session.add(review)
    db_session.commit()
    base = f"/api/v1/workspaces/{run.workspace_id}"
    response = client.post(base + f"/human-reviews/{review.id}/resolve", headers=headers,
                           json={"decision": "rejected", "comments": "Do not apply"})
    assert response.status_code == 200
    assert response.json()["run"]["status"] == "rejected"
    db_session.refresh(proposal)
    assert proposal.status == "rejected"
    assert db_session.scalar(select(func.count()).select_from(TaskNote)) == 0
