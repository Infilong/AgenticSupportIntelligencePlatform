import json
import os
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_agents import create_agent
from test_embedding_runtime import configured_client as configured_client
from test_retrieval import auth_headers, create_workspace, login, register, upload_document
from test_review_transactions import review_database as review_database

from app.core.language import SupportedLanguage
from app.models.agent import AgentConfig, GraphStep
from app.models.ai import AIRun, AIRunStatus
from app.models.budget import WorkspaceBudgetPolicy
from app.models.retrieval import RetrievalTrace
from app.models.workspace import Workspace
from app.services.embedding_attempts import EmbeddingAdmissionError, EmbeddingAttemptLedger
from app.services.embedding_transport import EmbeddingTransportError, OpenAIEmbeddingTransport

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires isolated PostgreSQL verification")


@pytest.mark.parametrize("limit", ["agent", "per_run_token_budget", "per_run_cost_budget"])
def test_graph_embedding_admission_enforces_each_run_limit(review_database, limit):
    engine, ids = review_database
    with Session(engine) as db:
        policy = WorkspaceBudgetPolicy(workspace_id=ids[0])
        db.add(policy)
        if limit == "agent":
            db.scalar(select(AgentConfig)).token_budget = 1
        else:
            setattr(policy, limit, 1 if "token" in limit else 0.00000001)
        db.commit()
    with pytest.raises(EmbeddingAdmissionError, match="budget_exceeded"):
        EmbeddingAttemptLedger(engine).begin(workspace_id=ids[0], language=SupportedLanguage.en,
            model="text-embedding-3-small", texts=["refund policy"], token_cost_per_1k=0.001,
            purpose="embedding_query", graph_run_id=ids[3])
    with Session(engine) as db:
        assert db.scalar(select(AIRun)) is None


@pytest.mark.parametrize("foreign_workspace", [False, True])
def test_unknown_or_foreign_graph_cannot_receive_embedding_usage(
    review_database, foreign_workspace,
):
    engine, ids = review_database
    workspace_id, run_id = ids[0], uuid4()
    if foreign_workspace:
        with Session(engine) as db:
            workspace = Workspace(name="Separate workspace", created_by_user_id=ids[2][0])
            db.add(workspace)
            db.commit()
            workspace_id, run_id = workspace.id, ids[3]
    with pytest.raises(EmbeddingAdmissionError, match="graph run was not found"):
        EmbeddingAttemptLedger(engine).begin(
            workspace_id=workspace_id, language=SupportedLanguage.en,
            model="text-embedding-3-small", texts=["query"], token_cost_per_1k=0.001,
            purpose="embedding_query", graph_run_id=run_id)


def test_pending_embedding_usage_consumes_remaining_run_allowance(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        db.add(WorkspaceBudgetPolicy(workspace_id=ids[0], per_run_token_budget=20))
        db.commit()
    ledger = EmbeddingAttemptLedger(engine)
    kwargs = dict(workspace_id=ids[0], graph_run_id=ids[3], language=SupportedLanguage.en,
                  model="text-embedding-3-small", texts=["refund policy"],
                  token_cost_per_1k=0.001, purpose="embedding_query")
    attempt_id = ledger.begin(**kwargs)
    with pytest.raises(EmbeddingAdmissionError, match="token_budget_exceeded"):
        ledger.begin(**kwargs)
    ledger.finish(workspace_id=ids[0], attempt_id=attempt_id, prompt_tokens=1, latency_ms=1)
    assert ledger.begin(**kwargs) != attempt_id


@pytest.mark.parametrize("mode", ["success", "provider_failure", "budget_denied"])
def test_graph_links_embedding_calls_and_routes_failure_to_review(
    configured_client, monkeypatch, mode,
):
    client, engine = configured_client
    calls = []
    question = "What is the refund policy?"

    def synthetic(self, **kwargs):
        calls.append(kwargs["texts"])
        if mode == "provider_failure" and kwargs["texts"] == [question]:
            raise EmbeddingTransportError("embedding_http_503")
        return {"model": kwargs["model"], "usage": {"prompt_tokens": 1, "total_tokens": 1},
                "data": [{"index": 0, "embedding": [1.0, 0.0, 0.0, 0.0]}]}

    monkeypatch.setattr(OpenAIEmbeddingTransport, "create", synthetic)
    register(client, "graph-embedding@example.com")
    token = login(client, "graph-embedding@example.com")
    workspace = create_workspace(client, token)
    upload_document(client, token, workspace["id"], title="Refund policy", language="en",
                    content="Refunds are available within seven days after purchase.")
    agent = create_agent(client, token, workspace["id"])
    original = EmbeddingAttemptLedger.begin

    def reduce_policy_before_query(ledger, **kwargs):
        if kwargs["purpose"] == "embedding_query":
            # A policy change after classification must still prevent the next paid dispatch.
            with Session(engine) as db:
                policy = db.scalar(select(WorkspaceBudgetPolicy).where(
                    WorkspaceBudgetPolicy.workspace_id == UUID(workspace["id"])))
                policy.per_run_token_budget = 1
                db.commit()
        return original(ledger, **kwargs)

    if mode == "budget_denied":
        monkeypatch.setattr(EmbeddingAttemptLedger, "begin", reduce_policy_before_query)
    base = f"/api/v1/workspaces/{workspace['id']}"
    response = client.post(f"{base}/agents/{agent['id']}/runs", headers=auth_headers(token),
                           json={"input_message": question})
    assert response.status_code == 201, response.text
    run = response.json()
    assert run["status"] == ("completed" if mode == "success" else "needs_human_review")
    with Session(engine) as db:
        step = db.scalar(select(GraphStep).where(GraphStep.graph_run_id == UUID(run["id"]),
                                                 GraphStep.step_name == "retrieve_evidence"))
        embedding = db.scalar(select(AIRun).where(AIRun.graph_run_id == UUID(run["id"]),
                                                 AIRun.purpose == "embedding_query"))
        if mode == "budget_denied":
            assert embedding is None and len(calls) == 1
            assert "token_budget_exceeded" in step.error_message
        else:
            assert embedding.graph_step_id == step.id and step.ai_run_id == embedding.id
            assert embedding.status == (AIRunStatus.succeeded if mode == "success"
                                         else AIRunStatus.uncertain)
        assert step.status == ("succeeded" if mode == "success" else "failed")
        trace = db.scalar(select(RetrievalTrace).where(
            RetrievalTrace.graph_run_id == UUID(run["id"])))
        assert trace is not None
        assert trace.outcome == ("succeeded" if mode == "success" else "failed")
        if mode != "success":
            assert json.loads(step.output_json)["retrieval_trace_id"] == str(trace.id)
        if mode != "success":
            assert trace.no_source and run["final_answer"] is None
    trace_response = client.get(f"{base}/agent-runs/{run['id']}/trace", headers=auth_headers(token))
    assert trace_response.status_code == 200
    purposes = {item["purpose"] for item in trace_response.json()["ai_runs"]}
    assert ("embedding_query" in purposes) is (mode != "budget_denied")
