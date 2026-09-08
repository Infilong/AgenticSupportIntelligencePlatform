import json

import pytest
from sqlalchemy import func, select
from test_agents import (
    auth_headers,
    create_agent,
    create_workspace,
    login,
    register,
)

from app.models.agent import GraphRun


@pytest.fixture
def language_context(client):
    register(client, "language-choice@example.test")
    token = login(client, "language-choice@example.test")
    workspace = create_workspace(client, token)
    for language, policy in (("ja", "返金は購入から7日以内に申請できます。"),
                             ("zh", "购买后7天内可以申请退款。")):
        uploaded = client.post(f"/api/v1/workspaces/{workspace['id']}/knowledge-documents",
                               headers=auth_headers(token), json={
            "title": "Policy " + language, "language": language, "content_type": "text/plain",
            "content": "返金申請：" + policy,
        })
        assert uploaded.status_code == 201
    agent = create_agent(client, token, workspace["id"])
    return f"/api/v1/workspaces/{workspace['id']}", auth_headers(token), agent["id"]


@pytest.mark.parametrize("requested,expected,source", [
    ("ja", "ja", "requested"), ("zh", "zh", "requested"), (None, "zh", "detected"),
])
def test_requested_language_controls_trace_retrieval_and_model(
    client, language_context, requested, expected, source,
):
    base, headers, agent = language_context
    payload = {"input_message": "返金申請"}
    if requested is not None:
        payload["language"] = requested
    response = client.post(base + f"/agents/{agent}/runs", headers=headers, json=payload)
    assert response.status_code == 201
    run = response.json()
    assert run["language"] == expected
    trace = client.get(base + f"/agent-runs/{run['id']}/trace", headers=headers).json()
    selection = json.loads(trace["steps"][0]["output_json"])
    assert selection["language_source"] == source
    retrieval = next(json.loads(step["output_json"]) for step in trace["steps"]
                     if step["step_name"] == "retrieve_evidence")
    assert retrieval["retrieved_chunks"]
    assert all(chunk["language"] == expected for chunk in retrieval["retrieved_chunks"])
    assert trace["ai_runs"] and all(row["language"] == expected for row in trace["ai_runs"])


def test_invalid_language_is_rejected_without_run(client, db_session, language_context):
    base, headers, agent = language_context
    before = db_session.scalar(select(func.count()).select_from(GraphRun))
    response = client.post(base + f"/agents/{agent}/runs", headers=headers,
                           json={"input_message": "返金申請", "language": "fr"})
    assert response.status_code == 422
    assert db_session.scalar(select(func.count()).select_from(GraphRun)) == before


def test_system_evaluation_preserves_declared_language(client, language_context):
    base, headers, agent = language_context
    response = client.post(base + "/evaluations", headers=headers, json={
        "name": "Japanese ambiguous input", "agent_id": agent, "modes": ["system_v1"],
        "jsonl_cases": json.dumps({"id": "kanji", "language": "ja", "input_message": "返金申請"}),
    })
    assert response.status_code == 201
    result = response.json()["results"][0]
    trace = client.get(base + f"/agent-runs/{result['graph_run_id']}/trace", headers=headers).json()
    assert trace["run"]["language"] == "ja"
    assert json.loads(trace["steps"][0]["output_json"])["language_source"] == "requested"


def test_requested_language_does_not_bypass_workspace_access(client, db_session, language_context):
    base, _, agent = language_context
    register(client, "language-outsider@example.test")
    token = login(client, "language-outsider@example.test")
    before = db_session.scalar(select(func.count()).select_from(GraphRun))
    response = client.post(base + f"/agents/{agent}/runs", headers=auth_headers(token),
                           json={"input_message": "返金申請", "language": "ja"})
    assert response.status_code == 404
    assert db_session.scalar(select(func.count()).select_from(GraphRun)) == before
