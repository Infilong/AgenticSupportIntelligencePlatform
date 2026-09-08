import json

import pytest
from sqlalchemy import select
from test_human_reviews import (
    auth_headers,
    create_agent,
    create_review_fixture,
    create_workspace,
    login,
    register,
)

from app.models.agent import Checkpoint, GraphRun, GraphStep, GraphStepStatus
from app.models.audit import AuditLog


@pytest.mark.parametrize("decision", ["approved", "edited"])
@pytest.mark.parametrize("answer,evidence,valid", [
    ("Seven days [Policy#chunk-0].", True, True),
    ("Seven days [Policy#chunk-0] and [Other#chunk-9].", True, False),
    ("Seven days [Policy#chunk-0].", False, False),
    ("Seven days [Policy#chunk-0].", "foreign", False),
    ("Seven days [Policy#chunk-0].", "malformed", False),
    ("Seven days [Policy#chunk-0].", "failed", False),
    ("A support specialist will follow up.", False, True),
    ("   ", True, False),
])
def test_review_answer_integrity(client, db_session, decision, answer, evidence, valid):
    user = register(client, "review-integrity@example.test")
    token = login(client, "review-integrity@example.test")
    workspace = create_workspace(client, token)
    agent = create_agent(client, token, workspace["id"])
    review = create_review_fixture(
        db_session, workspace_id=workspace["id"], agent_id=agent["id"],
        user_id=user["id"], message="Refund?", reason="citation_required",
        proposed_answer=answer,
    )
    run = db_session.get(GraphRun, review.graph_run_id)
    run.final_answer = None
    if evidence:
        evidence_workspace = review.workspace_id
        if evidence == "foreign":
            from uuid import UUID
            evidence_workspace = UUID(create_workspace(client, token, "Other")["id"])
        db_session.add(GraphStep(
            workspace_id=evidence_workspace, graph_run_id=run.id,
            step_name="compress_context", latency_ms=1,
            status=GraphStepStatus.failed if evidence == "failed" else GraphStepStatus.succeeded,
            input_json="{}",
            output_json="invalid" if evidence == "malformed" else json.dumps({
                "packed_context_chunks": [
                {"citation": "[Policy#chunk-0]", "content": "Seven days."},
            ]}),
        ))
    db_session.commit()
    url = f"/api/v1/workspaces/{workspace['id']}/human-reviews/{review.id}/resolve"
    response = client.post(url, headers=auth_headers(token), json={
        "decision": decision, "edited_answer": answer if decision == "edited" else None,
    })
    assert response.status_code == (200 if valid else 400)
    db_session.expire_all()
    if valid:
        assert run.final_answer == answer
        return
    assert response.json()["detail"]["code"] == "human_review_invalid_decision"
    assert review.reviewer_decision == "pending"
    assert review.resolved_at is None
    assert run.status == "needs_human_review"
    assert run.final_answer is None
    assert db_session.scalar(select(Checkpoint).where(Checkpoint.graph_run_id == run.id)) is None
    assert db_session.scalar(select(AuditLog).where(
        AuditLog.resource_id == str(review.id), AuditLog.action == "human_review.resolved",
    )) is None
    corrected = client.post(url, headers=auth_headers(token), json={
        "decision": "edited", "edited_answer": "A support specialist will follow up.",
    })
    assert corrected.status_code == 200
