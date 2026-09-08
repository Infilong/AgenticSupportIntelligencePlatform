"""Evaluation usage must agree with the model ledger, not step total tokens."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.core.language import SupportedLanguage
from app.models.ai import AIRun, AIRunStatus
from app.services.evaluation_usage import graph_model_usage
from tests.test_evaluations import (
    auth_headers,
    create_workspace,
    jsonl_content,
    login,
    register,
    upload_refund_documents,
)


@pytest.mark.parametrize("language,question", [
    ("en", "What is the refund policy?"),
    ("ja", "返金ポリシーを教えてください。"),
    ("zh", "退款政策是什么？"),
])
def test_system_evaluation_counts_ledger_prompt_tokens(client, db_session, language, question):
    register(client, "usage@example.test")
    token = login(client, "usage@example.test")
    workspace = create_workspace(client, token)
    upload_refund_documents(client, token, workspace["id"])
    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/evaluations",
        headers=auth_headers(token),
        json={"name": "Ledger usage", "modes": ["system_v1"],
              "jsonl_cases": jsonl_content({"id": "usage", "language": language,
                                            "input_message": question})},
    )
    assert response.status_code == 201
    body = response.json()
    result = body["results"][0]
    calls = list(db_session.scalars(select(AIRun).where(
        AIRun.workspace_id == UUID(workspace["id"]),
        AIRun.graph_run_id == UUID(result["graph_run_id"]),
    )))
    assert calls
    assert sum(call.completion_tokens for call in calls) > 0
    expected = sum(call.prompt_tokens for call in calls)
    assert result["prompt_tokens"] == expected
    assert result["estimated_cost"] == pytest.approx(sum(call.estimated_cost for call in calls))
    metric = next(row for row in body["metrics"]
                  if row["metric_name"] == "average_prompt_tokens")
    assert metric["metric_value"] == expected


def test_graph_usage_is_scoped_and_includes_failed_and_cached_ledger_calls(client, db_session):
    register(client, "scoped-usage@example.test")
    token = login(client, "scoped-usage@example.test")
    workspace = UUID(create_workspace(client, token)["id"])
    other = UUID(create_workspace(client, token, "Other")["id"])
    graph = uuid4()
    assert graph_model_usage(db_session, workspace, graph) == (0, 0.0)
    for scope, run, status, cached, tokens in [
        (workspace, graph, AIRunStatus.succeeded, False, 11),
        (workspace, graph, AIRunStatus.failed, False, 7),
        (workspace, graph, AIRunStatus.succeeded, True, 5),
        (other, graph, AIRunStatus.succeeded, False, 1000),
        (workspace, uuid4(), AIRunStatus.succeeded, False, 1000),
    ]:
        db_session.add(AIRun(
            workspace_id=scope, graph_run_id=run, provider="mock", model="mock-standard",
            purpose="test", language=SupportedLanguage.en, prompt_tokens=tokens,
            completion_tokens=3, total_tokens=tokens + 3, estimated_cost=tokens / 1000,
            latency_ms=1, cache_hit=cached, status=status,
        ))
    db_session.commit()
    tokens, cost = graph_model_usage(db_session, workspace, graph)
    assert tokens == 23
    assert cost == pytest.approx(0.023)
