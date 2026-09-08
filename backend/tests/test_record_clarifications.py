"""Clarification replies continue an input without replacing it or gaining authority."""

import json
from uuid import UUID, uuid4

from sqlalchemy import func, select
from test_admin_hierarchy import account
from test_records_api import fixture_records

from app.models.agent import GraphRun
from app.models.task import SupportTask, TaskExecution
from app.models.task_attempt import TaskAttempt
from app.services.graph_outcome import publish_graph_outcome
from app.services.support_agent_graph import SupportAgentGraphRunner


def waiting(client, db):
    base, agent, headers = fixture_records(client)
    response = client.post(base + "/records", headers=headers, json={
        "agent_id": agent, "request_key": "input", "input": {"content": "w"}})
    assert response.status_code == 202
    record = response.json()
    run = db.get(GraphRun, UUID(record["latest_run_id"]))
    state = json.loads(db.get(TaskExecution, run.id).initial_state_json)
    publish_graph_outcome(db, run, SupportAgentGraphRunner(db).run(state))
    return base, headers, record, run


def test_clarification_preserves_original_and_deduplicates_reply(client, db_session):
    base, headers, original, parent = waiting(client, db_session)
    url = base + "/records/" + original["id"] + "/clarifications"
    body = {"run_id": str(parent.id), "request_key": "reply", "reply": "What is the refund policy?"}
    response = client.post(url, headers=headers, json=body)
    assert response.status_code == 202, response.text
    record = response.json()
    assert record["id"] == original["id"]
    assert record["input"] == original["input"]
    assert record["attempt_count"] == 2
    assert record["status"] == "queued"
    assert client.post(url, headers=headers, json=body).json() == record
    assert client.post(url, headers=headers, json={**body, "reply": "Different"}).status_code == 409
    assert client.post(url, headers=headers,
                       json={**body, "request_key": "second"}).status_code == 409
    child_id = UUID(record["latest_run_id"])
    attempt = db_session.get(TaskAttempt, child_id)
    assert attempt.clarification_reply == body["reply"]
    assert attempt.corrected_instructions == ""
    state = json.loads(db_session.get(TaskExecution, child_id).initial_state_json)
    assert state["input_message"] == body["reply"]
    assert state["task_history"]["clarification"]["original_input"] == "w"
    assert db_session.get(GraphRun, parent.id).route_decision == "clarification_received"
    assert db_session.scalar(select(func.count()).select_from(SupportTask)) == 1
    detail = client.get(base + f"/task-runs/{child_id}", headers=headers).json()
    assert detail["clarification_reply"] == body["reply"]


def test_clarification_denies_viewer_foreign_attempt_and_blank_reply(client, db_session):
    base, headers, original, parent = waiting(client, db_session)
    _, email, viewer = account(client, "clarification-viewer")
    client.post(base + "/members", headers=headers, json={"email": email, "role": "viewer"})
    url = base + "/records/" + original["id"] + "/clarifications"
    body = {"run_id": str(parent.id), "request_key": "reply", "reply": "Refund policy?"}
    assert client.post(url, headers=viewer, json=body).status_code == 403
    assert client.post(url, headers=headers,
                       json={**body, "run_id": str(uuid4())}).status_code == 404
    assert client.post(url, headers=headers, json={**body, "reply": " "}).status_code == 409
    assert db_session.get(GraphRun, parent.id).status == "awaiting_clarification"
    assert db_session.scalar(select(func.count()).select_from(TaskAttempt)) == 0
