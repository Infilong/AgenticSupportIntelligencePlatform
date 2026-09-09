import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.jobs.models import Job
from app.modules.knowledge.models import Document, DocumentVersion
from app.modules.support.models import Handoff, RunStep, SupportRun
from app.profile_release import profile
from tests.integration.conftest import login
from tests.integration.test_knowledge import add_version, ingest


def prepare(system):
    documents = []
    for _ in range(2):
        version = add_version(system)
        assert ingest(system)
        documents.append(version.document_id)
    headers = login(system["client"], "operator")
    runs = []
    for _ in range(5):
        response = system["client"].post(
            f"/api/workspaces/{system['workspace']}/messages",
            headers={**headers, "Idempotency-Key": uuid.uuid4().hex},
            json={"original": "w", "language": "en"},
        )
        assert response.status_code == 202
        runs.append(response.json())
    return runs, documents


def test_scoped_read_only_snapshot_preserves_unknown_and_negative_timing(system):
    runs, documents = prepare(system)
    with Session(system["engine"]) as db, db.begin():
        for index, milliseconds in [(1, 100), (2, -100)]:
            job = db.get(Job, uuid.UUID(runs[index]["job_id"]))
            db.add(
                RunStep(
                    workspace_id=system["workspace"],
                    run_id=uuid.UUID(runs[index]["run_id"]),
                    job_id=job.id,
                    job_attempt=1,
                    node="test_observation",
                    status="succeeded",
                    created_at=job.created_at + timedelta(milliseconds=milliseconds),
                )
            )
    with system["engine"].connect() as connection, connection.begin():
        result = profile(
            connection, system["workspace"], [uuid.UUID(row["run_id"]) for row in runs], documents
        )
        by_id = {str(row["id"]): row for row in result["runs"]}
        assert by_id[runs[0]["run_id"]]["admission_to_first_node_ms"] is None
        assert by_id[runs[1]["run_id"]]["admission_to_first_node_ms"] == 100
        assert by_id[runs[2]["run_id"]]["admission_to_first_node_ms"] == -100
        assert all(row["admission_to_handoff_ms"] is None for row in result["runs"])
        assert result["admitted_ingestion_window_overlaps_support_window"] is None
        assert result["current_corpus"]["active_documents"] == 2
        assert result["current_corpus"]["active_chunks"] >= 2
        assert result["current_corpus"]["bytes"] == sum(row["bytes"] for row in result["documents"])
        with pytest.raises(DBAPIError):
            connection.execute(text("UPDATE workspaces SET name=name"))


@pytest.mark.parametrize("mismatch", ["workspace", "run", "document"])
def test_foreign_or_missing_ids_never_produce_a_partial_report(system, mismatch):
    runs, documents = prepare(system)
    ids = [uuid.UUID(row["run_id"]) for row in runs]
    workspace = system["foreign"] if mismatch == "workspace" else system["workspace"]
    if mismatch == "run":
        ids[0] = uuid.uuid4()
    if mismatch == "document":
        documents[0] = uuid.uuid4()
    with system["engine"].connect() as connection, connection.begin():
        with pytest.raises(ValueError, match="unavailable"):
            profile(connection, workspace, ids, documents)


def test_overlap_uses_recorded_intervals_instead_of_test_launch_order(system):
    runs, documents = prepare(system)
    ids = [uuid.UUID(row["run_id"]) for row in runs]
    start = datetime(2026, 1, 1, tzinfo=UTC)
    with Session(system["engine"]) as db, db.begin():
        for run_id in ids:
            run = db.get(SupportRun, run_id)
            run.created_at = start + timedelta(seconds=10)
            db.get(Job, run.job_id).created_at = run.created_at
            db.add(
                Handoff(
                    workspace_id=system["workspace"],
                    run_id=run_id,
                    context={},
                    context_hash="a" * 64,
                    created_at=start + timedelta(seconds=20),
                )
            )
        background_id = db.get(Document, documents[1]).active_version_id
        version = db.get(DocumentVersion, background_id)
        version.created_at = start
        version.indexed_at = start + timedelta(seconds=5)
    with system["engine"].connect() as connection, connection.begin():
        assert (
            profile(connection, system["workspace"], ids, documents)[
                "admitted_ingestion_window_overlaps_support_window"
            ]
            is False
        )
    with Session(system["engine"]) as db, db.begin():
        db.get(DocumentVersion, background_id).indexed_at = start + timedelta(seconds=15)
    with system["engine"].connect() as connection, connection.begin():
        assert (
            profile(connection, system["workspace"], ids, documents)[
                "admitted_ingestion_window_overlaps_support_window"
            ]
            is True
        )
