"""Execution history must not depend on the wall clock moving forward."""
# ruff: noqa: F811

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import event, update
from test_requested_language import language_context  # noqa: F401

from app.models.agent import GraphStep


@pytest.mark.parametrize("backward", [True, False], ids=["backward-clock", "tied-clock"])
def test_trace_preserves_execution_and_parent_order(client, language_context, backward):
    base, headers, agent = language_context
    inserted = []

    def set_clock(mapper, connection, step):
        step.created_at = datetime(2026, 9, 8, tzinfo=UTC) - timedelta(
            seconds=len(inserted) if backward else 0
        )
        inserted.append(step)

    event.listen(GraphStep, "before_insert", set_clock)
    try:
        response = client.post(base + f"/agents/{agent}/runs", headers=headers,
                               json={"input_message": "返金申請", "language": "ja"})
    finally:
        event.remove(GraphStep, "before_insert", set_clock)
    assert response.status_code == 201
    trace = client.get(base + f"/agent-runs/{response.json()['id']}/trace", headers=headers)
    assert trace.status_code == 200
    steps = trace.json()["steps"]
    assert len(steps) >= 7
    assert [step["id"] for step in steps] == [str(step.id) for step in inserted]
    assert steps[0]["step_name"] == "detect_language"
    assert [step["sequence"] for step in steps] == list(range(1, len(steps) + 1))
    assert steps[0]["parent_span_id"] is None
    for previous, current in zip(steps, steps[1:], strict=False):
        assert current["parent_span_id"] == previous["span_id"]


def test_legacy_trace_exposes_unknown_sequence(client, db_session, language_context):
    base, headers, agent = language_context
    response = client.post(base + f"/agents/{agent}/runs", headers=headers,
                           json={"input_message": "返金申請", "language": "ja"})
    assert response.status_code == 201
    db_session.execute(update(GraphStep).values(sequence=None))
    db_session.commit()
    response = client.get(base + f"/agent-runs/{response.json()['id']}/trace", headers=headers)
    assert response.status_code == 200
    steps = response.json()["steps"]
    assert steps and all(step["sequence"] is None for step in steps)
