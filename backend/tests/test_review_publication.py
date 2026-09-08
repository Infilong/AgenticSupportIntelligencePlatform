import os
from uuid import UUID

import pytest
from sqlalchemy import event, select
from test_human_reviews import create_agent, create_workspace, login, register
from test_review_transactions import review_database as review_database

from app.models.agent import GraphRun, GraphRunStatus
from app.models.review import GuardrailResult, HumanReview
from app.models.user import User
from app.services.agent_service import AgentService
from app.services.support_agent_graph import SupportAgentGraphRunner


@pytest.fixture
def publication_context(client, db_session, monkeypatch):
    user = register(client, "publisher@example.test")
    token = login(client, "publisher@example.test")
    workspace = create_workspace(client, token)
    agent = create_agent(client, token, workspace["id"])

    def final_state(self, state):
        # Exercise final persistence without model calls; final guardrails must override this draft.
        return {**state, "detected_language": state["input_message"],
                "route_decision": "finalize", "final_answer": "Unsupported draft",
                "draft_answer": "Unsupported draft", "citations": [], "no_source": True,
                "confidence_score": 0.1}

    monkeypatch.setattr(SupportAgentGraphRunner, "run", final_state)
    return dict(workspace_id=UUID(workspace["id"]), agent_id=UUID(agent["id"]),
                current_user=db_session.get(User, UUID(user["id"])))


@pytest.mark.parametrize("language", ["en", "ja", "zh"])
@pytest.mark.parametrize("failed_model", [GuardrailResult, HumanReview])
def test_failed_publication_never_exposes_success_or_orphan_review(
    db_session, publication_context, language, failed_model,
):
    def reject_insert(mapper, connection, target):
        raise RuntimeError("injected publication storage failure")

    event.listen(failed_model, "before_insert", reject_insert)
    try:
        with pytest.raises(RuntimeError, match="injected publication storage failure"):
            AgentService(db_session).run_agent(**publication_context, input_message=language)
    finally:
        event.remove(failed_model, "before_insert", reject_insert)
        db_session.rollback()
    run = db_session.scalar(select(GraphRun))
    assert run.status == GraphRunStatus.failed
    assert run.route_decision == "publication_failed"
    assert run.final_answer is None
    assert db_session.scalars(select(HumanReview)).all() == []
    assert db_session.scalars(select(GuardrailResult)).all() == []


@pytest.mark.parametrize("language", ["en", "ja", "zh"])
def test_review_and_guardrails_publish_with_final_run(db_session, publication_context, language):
    run = AgentService(db_session).run_agent(**publication_context, input_message=language)
    assert run.status == GraphRunStatus.needs_human_review
    assert run.language == language
    assert run.final_answer is None
    review = db_session.scalar(select(HumanReview))
    assert review.graph_run_id == run.id
    assert review.workspace_id == run.workspace_id
    assert db_session.scalars(select(GuardrailResult)).all()


def test_failure_record_outage_preserves_original_error(db_session, publication_context, caplog):
    def reject_guardrail(mapper, connection, target):
        raise RuntimeError("original publication failure")

    def reject_failure_record(mapper, connection, target):
        if target.status == GraphRunStatus.failed:
            raise OSError("secondary storage failure")

    event.listen(GuardrailResult, "before_insert", reject_guardrail)
    event.listen(GraphRun, "before_update", reject_failure_record)
    try:
        with pytest.raises(RuntimeError, match="original publication failure"):
            AgentService(db_session).run_agent(**publication_context, input_message="en")
    finally:
        event.remove(GuardrailResult, "before_insert", reject_guardrail)
        event.remove(GraphRun, "before_update", reject_failure_record)
    assert "graph_publication_failure_record_failed error_type=OSError" in caplog.text
    assert "secondary storage failure" not in caplog.text
    assert db_session.scalar(select(GraphRun)).status == GraphRunStatus.running


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
def test_other_sessions_never_see_review_status_before_queue_insert(review_database, monkeypatch):
    from sqlalchemy.orm import Session

    engine, ids = review_database
    observed = []

    def inspect_visibility(mapper, connection, review):
        with engine.connect() as reader:
            observed.append(reader.scalar(select(GraphRun.status).where(
                GraphRun.id == review.graph_run_id
            )))

    monkeypatch.setattr(SupportAgentGraphRunner, "run", lambda self, state: {
        **state, "detected_language": "en", "route_decision": "human_review",
        "draft_answer": None, "no_source": True,
    })
    event.listen(HumanReview, "before_insert", inspect_visibility)
    try:
        with Session(engine) as db:
            original = db.get(GraphRun, ids[3])
            run = AgentService(db).run_agent(
                workspace_id=ids[0], agent_id=original.agent_config_id, input_message="Unknown?",
                current_user=db.get(User, ids[2][0]),
            )
            assert run.status == GraphRunStatus.needs_human_review
    finally:
        event.remove(HumanReview, "before_insert", inspect_visibility)
    assert observed == [GraphRunStatus.running]
