"""Incomplete input requests information without generating a review or a model call."""

import json

import pytest
from sqlalchemy import func, select
from test_task_admission import setup

from app.models.agent import GraphStep
from app.models.ai import AIRun
from app.models.review import HumanReview
from app.models.task import TaskExecution
from app.services.graph_outcome import publish_graph_outcome
from app.services.input_clarification import needs_input_clarification
from app.services.support_agent_graph import SupportAgentGraphRunner
from app.services.task_admission import admit_task
from app.services.task_control import request_stop


@pytest.mark.parametrize("message", ["w", "?", "...", "！"])
def test_incomplete_input_requests_clarification_without_review(client, db_session, message):
    args = {**setup(client), "message": message}
    _, run = admit_task(db_session, **args)
    initial = json.loads(db_session.get(TaskExecution, run.id).initial_state_json)
    result = SupportAgentGraphRunner(db_session).run(initial)
    published = publish_graph_outcome(db_session, run, result)
    assert published.status == "awaiting_clarification"
    assert published.final_answer
    assert published.route_decision == "clarification"
    assert db_session.scalar(select(func.count()).select_from(HumanReview)) == 0
    assert db_session.scalar(select(func.count()).select_from(AIRun)) == 0
    steps = list(db_session.scalars(select(GraphStep.step_name)
        .where(GraphStep.graph_run_id == run.id).order_by(GraphStep.sequence)))
    assert steps == ["request_clarification"]
    assert result["language_source"] == "default"
    stopped = request_stop(db_session, workspace_id=run.workspace_id, run_id=run.id,
                           user_id=run.user_id)
    assert stopped.status == "stopped"


@pytest.mark.parametrize("message", ["退款", "返金", "税", "Hi", "Refund?", "3 days", "API"])
def test_short_meaningful_input_is_not_rejected_by_length(message):
    assert not needs_input_clarification({"input_message": message})


def test_single_letter_followup_is_not_treated_as_standalone():
    assert not needs_input_clarification({"input_message": "A", "task_history": {"task_id": "x"}})
