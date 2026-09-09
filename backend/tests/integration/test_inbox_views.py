"""Real PostgreSQL projections over explicit stored-state fixtures, not workflow execution."""

import uuid

from sqlalchemy.orm import Session

from app.jobs.models import Job
from app.modules.support.models import Message, SupportRun
from tests.integration.conftest import login


def populate(system):
    client = system["client"]
    auth = login(client, "operator")
    path = f"/api/workspaces/{system['workspace']}/messages"
    cases = [
        ("queued", None, "queued", "processing"),
        ("queued", None, "running", "processing"),
        ("queued", None, "failed", "failed"),
        ("queued", None, "cancelled", "all"),
        ("waiting_for_input", None, "succeeded", "attention"),
        ("awaiting_review", "grounded_draft", "succeeded", "attention"),
        ("completed", "clarification_needed", "succeeded", "attention"),
        ("completed", "insufficient_evidence", "succeeded", "attention"),
        ("completed", "approved_response", "succeeded", "ready"),
        ("queued", "grounded_draft", "failed", "failed"),
        ("rejected", "rejected_response", "succeeded", "all"),
        ("cancelled", None, "cancelled", "all"),
    ]
    expected = {view: set() for view in ("all", "attention", "ready", "processing", "failed")}
    for index, (state, outcome, job_state, view) in enumerate(cases):
        response = client.post(
            path,
            headers={**auth, "Idempotency-Key": f"view-{index}"},
            json={"original": f"Unique request {index:02d} refund policy", "language": "en"},
        )
        assert response.status_code == 202, response.text
        run_id = response.json()["run_id"]
        with Session(system["engine"]) as db, db.begin():
            run = db.get(SupportRun, uuid.UUID(run_id))
            run.state, run.outcome = state, outcome
            db.get(Job, run.job_id).state = job_state
        expected["all"].add(run_id)
        expected[view].add(run_id)
    return path, expected


def test_inbox_views_filter_latest_state_with_matching_counts_and_pagination(system):
    path, expected = populate(system)
    client = system["client"]
    for view, ids in expected.items():
        response = client.get(path, params={"view": view, "limit": 50})
        assert response.status_code == 200
        page = response.json()
        assert page["total"] == len(ids)
        assert {row["run_id"] for row in page["items"]} == ids
        first = client.get(path, params={"view": view, "limit": 1}).json()
        rest = client.get(path, params={"view": view, "offset": 1, "limit": 50}).json()
        assert first["total"] == rest["total"] == len(ids)
        assert {row["run_id"] for row in first["items"] + rest["items"]} == ids
    match = client.get(path, params={"search": "08", "view": "ready"}).json()
    assert match["total"] == 1 and len(match["items"]) == 1
    assert client.get(path, params={"search": "08", "view": "attention"}).json()["total"] == 0
    assert client.get(path, params={"search": "%", "view": "all"}).json()["total"] == 0
    assert client.get(path, params={"view": "ready", "offset": 10}).json()["items"] == []


def test_inbox_views_are_validated_and_workspace_authorized(system):
    path, expected = populate(system)
    client = system["client"]
    assert client.get(path, params={"view": "unknown"}).status_code == 422
    login(client, "viewer")
    assert client.get(path, params={"view": "ready"}).json()["total"] == len(expected["ready"])
    assert client.get(f"/api/workspaces/{system['foreign']}/messages?view=all").status_code == 404
    login(client, "other")
    assert client.get(path, params={"view": "all"}).status_code == 404
    assert client.get(f"/api/workspaces/{system['foreign']}/messages?view=all").json()["total"] == 0


def test_new_attempt_moves_message_between_views_without_counting_old_outcome(system):
    path, expected = populate(system)
    client = system["client"]
    # Initial clarification outcome permits a real linked reply without processing the fixture.
    current = next(
        row
        for row in client.get(path, params={"view": "attention"}).json()["items"]
        if row["outcome"] == "clarification_needed"
    )
    auth = login(client, "operator")
    response = client.post(
        f"/api/workspaces/{system['workspace']}/runs/{current['run_id']}/attempts",
        headers={**auth, "Idempotency-Key": "new-view-attempt"},
        json={"action": "clarify", "clarification": "It was purchased yesterday."},
    )
    assert response.status_code == 202, response.text
    attention = client.get(path, params={"view": "attention"}).json()
    processing = client.get(path, params={"view": "processing"}).json()
    assert attention["total"] == len(expected["attention"]) - 1
    assert processing["total"] == len(expected["processing"]) + 1
    assert current["run_id"] not in {row["run_id"] for row in attention["items"]}
    assert response.json()["run_id"] in {row["run_id"] for row in processing["items"]}
    assert client.get(path).json()["total"] == len(expected["all"])


def test_all_count_and_page_consistently_exclude_a_message_without_a_run(system):
    path, expected = populate(system)
    with Session(system["engine"]) as db, db.begin():
        db.add(
            Message(
                workspace_id=system["workspace"],
                actor_id=system["users"]["operator"].id,
                original="Unprocessed fixture",
                language="en",
                submission_key="unprocessed",
                input_hash="0" * 64,
            )
        )
    page = system["client"].get(path, params={"limit": 50}).json()
    assert page["total"] == len(page["items"]) == len(expected["all"])
    assert system["client"].get(path, params={"search": "Unprocessed"}).json() == {"items": [], "total": 0}
