import json
from uuid import UUID

from sqlalchemy import select
from test_agents import auth_headers, create_agent, create_workspace, login, register

from app.core.trace_redaction import redact_trace
from app.models.agent import Checkpoint, GraphStep


def test_nested_json_redaction_preserves_citations_accounting_and_languages():
    payload = {"api_key": "synthetic-secret", "prompt_tokens": 24,
               "content": "連絡先 customer@example.test 退款7天",
               "citation": "document:123:v2#chunk-1", "private_chain_of_thought": "hidden",
               "nested": json.dumps({"Authorization": "Bearer synthetic", "value": 3})}
    original = json.dumps(payload)
    result = redact_trace(payload)
    assert result["api_key"] == "[REDACTED]"
    assert result["private_chain_of_thought"] == "[REDACTED]"
    assert result["prompt_tokens"] == 24
    assert result["content"] == "連絡先 [REDACTED] 退款7天"
    assert result["citation"] == payload["citation"]
    assert json.loads(result["nested"]) == {"Authorization": "[REDACTED]", "value": 3}
    assert json.dumps(payload) == original


def test_plain_errors_and_malformed_json_do_not_expose_recognized_credentials():
    value = 'password="synthetic password" api_key=synthetic-key Bearer abc.def sk-abcdefghijklmnop'
    result = redact_trace(value)
    assert all(secret not in result for secret in ["synthetic", "abc.def", "sk-abcdefghijklmnop"])
    assert "customer@example.test" not in redact_trace('{broken customer@example.test')


def test_trace_api_redacts_final_nested_output_without_rewriting_storage(client, db_session):
    register(client, "trace-owner@example.test")
    token = login(client, "trace-owner@example.test")
    workspace = create_workspace(client, token)
    agent = create_agent(client, token, workspace["id"])
    base = f"/api/v1/workspaces/{workspace['id']}"
    admitted = client.post(base + f"/agents/{agent['id']}/runs", headers=auth_headers(token),
                           json={"input_message": "What is the refund policy?"})
    assert admitted.status_code == 201
    run_id = UUID(admitted.json()["id"])
    step = db_session.scalar(select(GraphStep).where(GraphStep.graph_run_id == run_id))
    checkpoint = db_session.scalar(select(Checkpoint).where(Checkpoint.graph_run_id == run_id))
    assert step is not None and checkpoint is not None
    step.error_message = "Provider failed api_key=synthetic-private-key"
    checkpoint.state_json = json.dumps({"api_key": "synthetic-checkpoint-key",
                                        "content": "Email customer@example.test"})
    db_session.commit()
    response = client.get(base + f"/agent-runs/{run_id}/trace", headers=auth_headers(token))
    assert response.status_code == 200
    assert all(secret not in response.text for secret in (
        "synthetic-private-key", "synthetic-checkpoint-key", "customer@example.test"))
    assert "[REDACTED]" in response.text
    db_session.refresh(step)
    db_session.refresh(checkpoint)
    assert "synthetic-private-key" in step.error_message
    assert "synthetic-checkpoint-key" in checkpoint.state_json
    assert client.get(base + f"/agent-runs/{run_id}/trace").status_code == 401
    register(client, "trace-outsider@example.test")
    outsider = login(client, "trace-outsider@example.test")
    assert client.get(base + f"/agent-runs/{run_id}/trace",
                      headers=auth_headers(outsider)).status_code == 404
