from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.modules.support.context import digest
from app.modules.support.models import Handoff, RunStep
from tests.integration.conftest import login
from tests.integration.review_helpers import decision_payload, run_review
from tests.integration.support_helpers import base, create, draft_payload, prepare, run_support


@pytest.mark.parametrize("stage", ["completed_draft", "queued_contribution"])
def test_legacy_draft_transition_preserves_evidence_and_requires_admin(system, monkeypatch, stage):
    prepare(system)
    run = create(system)
    assert run_support(system)
    client, path = system["client"], base(system, run)
    auth = login(client)
    handoff = client.get(path + "/development-handoff").json()
    payload = draft_payload(handoff)
    assert (
        client.post(path + f"/development-handoff/{handoff['id']}", headers=auth, json=payload).status_code
        == 202
    )
    # Legacy contributions predate the routing annotation. Preserve their real stored shape.
    with Session(system["engine"]) as db, db.begin():
        record = db.scalar(select(Handoff))
        record.response = {key: value for key, value in record.response.items() if key != "review_category"}
        record.response_hash = digest(
            {"contributor": str(record.contributor_id), "response": record.response}
        )
    if stage == "completed_draft":
        # Exercise a real completed generation checkpoint without creating the new review graph.
        with monkeypatch.context() as patch:
            patch.setattr("app.modules.support.processing.wait_for_review", lambda *args: None)
            assert run_support(system)
        before = client.get(path).json()
    with system["engine"].begin() as connection:
        config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
        config.attributes["connection"] = connection
        command.downgrade(config, "0007_support")
        old = connection.execute(text("SELECT state, draft, finished_at FROM support_runs")).one()
        assert old.state == ("draft" if stage == "completed_draft" else "queued")
        if stage == "completed_draft":
            assert old.draft == before["draft"] and old.finished_at is not None
        command.upgrade(config, "head")
    if stage == "queued_contribution":
        assert run_support(system)
    draft = client.get(path).json()
    assert draft["state"] == "awaiting_review" and draft["review_kind"] == "unclassified"
    assert draft["draft"] == payload["answer"] and draft["reviewed_response"] is None
    if stage == "completed_draft":
        assert draft["citations"] == before["citations"]
    with Session(system["engine"]) as db:
        generation_steps = len(
            list(db.scalars(select(RunStep).where(RunStep.node == "development_generation")))
        )
    decision = decision_payload(draft)
    assert client.post(path + "/review", headers=login(client, "operator"), json=decision).status_code == 403
    assert client.post(path + "/review", headers=login(client), json=decision).status_code == 202
    worked, errors = run_review(system)
    assert worked and not errors, errors
    final = client.get(path).json()
    assert final["reviewed_response"] == payload["answer"] and final["citations"] == draft["citations"]
    with Session(system["engine"]) as db:
        assert (
            len(list(db.scalars(select(RunStep).where(RunStep.node == "development_generation"))))
            == generation_steps
        )
