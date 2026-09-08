from uuid import UUID

import pytest
from sqlalchemy import select
from test_human_reviews import (
    auth_headers,
    create_agent,
    create_workspace,
    login,
    register,
    upload_document,
)

from app.models.agent import AgentConfig, GraphStep
from app.models.ai import AIRun
from app.models.budget import WorkspaceBudgetPolicy
from app.models.reservation import ModelCallReservation
from app.models.review import HumanReview


@pytest.fixture
def graph_budget_context(client):
    register(client, "budget-runtime@example.test")
    token = login(client, "budget-runtime@example.test")
    workspace = create_workspace(client, token)
    agent = create_agent(client, token, workspace["id"])
    return token, workspace["id"], agent["id"]


def run(client, context):
    token, workspace, agent = context
    response = client.post(f"/api/v1/workspaces/{workspace}/agents/{agent}/runs",
                           headers=auth_headers(token),
                           json={"input_message": "What is the refund policy?"})
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.parametrize("limit,reason", [
    ("agent", "token_budget_exceeded"),
    ("per_run_token_budget", "token_budget_exceeded"),
    ("per_run_cost_budget", "cost_budget_exceeded"),
    ("monthly_token_budget", "monthly_token_budget_exceeded"),
    ("monthly_cost_budget", "monthly_cost_budget_exceeded"),
])
def test_budget_denial_skips_provider_and_routes_to_review(
    client, db_session, graph_budget_context, limit, reason,
):
    _, workspace, agent_id = graph_budget_context
    policy = WorkspaceBudgetPolicy(workspace_id=UUID(workspace))
    db_session.add(policy)
    if limit == "agent":
        db_session.get(AgentConfig, UUID(agent_id)).token_budget = 1
    else:
        setattr(policy, limit, 1 if "token" in limit else 0.00000001)
    db_session.commit()
    result = run(client, graph_budget_context)
    assert result["status"] == "needs_human_review"
    assert db_session.scalars(select(AIRun)).all() == []
    reservation = db_session.scalar(select(ModelCallReservation))
    assert reservation.status == "denied"
    assert reservation.denial_reason == reason
    review = db_session.scalar(select(HumanReview))
    assert "model_budget_failure" in review.reason
    step = db_session.scalar(select(GraphStep).where(GraphStep.step_name == "classify_intent"))
    assert step.status == "failed" and reason in step.error_message


def test_classification_and_drafting_share_one_run_budget(client, db_session, graph_budget_context):
    token, workspace, _ = graph_budget_context
    upload_document(client, token, workspace)
    initial = run(client, graph_budget_context)
    initial_calls = db_session.scalars(select(AIRun).where(
        AIRun.graph_run_id == UUID(initial["id"]))).all()
    assert {call.purpose for call in initial_calls} == {"classification", "draft_response"}
    reservations = db_session.scalars(select(ModelCallReservation)).all()
    assert len(reservations) == 2
    assert all(row.status == "consumed" and row.ai_run_id for row in reservations)
    policy = db_session.scalar(select(WorkspaceBudgetPolicy))
    policy.per_run_token_budget = sum(call.total_tokens for call in initial_calls) - 1
    db_session.commit()
    second = run(client, graph_budget_context)
    calls = db_session.scalars(select(AIRun).where(AIRun.graph_run_id == UUID(second["id"]))).all()
    assert [call.purpose for call in calls] == ["classification"]
    denial = db_session.scalar(select(ModelCallReservation).where(
        ModelCallReservation.graph_run_id == UUID(second["id"]),
        ModelCallReservation.status == "denied"))
    assert denial.purpose == "draft_response"
    assert second["status"] == "needs_human_review" and second["final_answer"] is None
