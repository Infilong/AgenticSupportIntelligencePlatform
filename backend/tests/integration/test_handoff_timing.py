from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.support.models import Handoff
from tests.integration.review_helpers import ready_draft


@pytest.mark.parametrize("seconds", [-1, 0, 90])
def test_handoff_timing_preserves_timestamps_and_reports_clock_anomaly(system, seconds):
    path, _ = ready_draft(system)
    created = datetime(2026, 9, 9, 0, 0, tzinfo=UTC)
    submitted = created + timedelta(seconds=seconds)
    with Session(system["engine"]) as db, db.begin():
        handoff = db.scalar(select(Handoff))
        handoff.created_at, handoff.submitted_at = created, submitted
    value = system["client"].get(path).json()["handoff"]
    assert datetime.fromisoformat(value["created_at"]) == created
    assert datetime.fromisoformat(value["submitted_at"]) == submitted
    assert value["timing_status"] == ("clock_anomaly" if seconds < 0 else "recorded")
    assert value["handoff_elapsed_ms"] == (None if seconds < 0 else seconds * 1000)
