import json
import os
import subprocess
import sys
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.evaluations.models import EvaluationRecord
from app.modules.evaluations.service import register
from app.modules.knowledge.retrieval_models import RetrievalTrace
from app.modules.workspaces.models import Membership
from tests.evaluation_fixture import report
from tests.integration.conftest import login


def prepare(system):
    data = report(system["workspace"])
    with Session(system["engine"]) as db, db.begin():
        for strategy in data["strategies"].values():
            for case in [*strategy["cases"], *strategy["negative_probes"]]:
                trace = case["trace"]
                db.add(
                    RetrievalTrace(
                        id=uuid.UUID(trace["id"]),
                        workspace_id=system["workspace"],
                        actor_id=system["users"]["admin"].id,
                        query=trace["query"],
                        status=trace["status"],
                        strategy=trace["strategy"],
                    )
                )
    return data


def test_register_read_idempotency_isolation_revocation(system):
    data = prepare(system)
    raw = json.dumps(data).encode()
    with Session(system["engine"]) as db, db.begin():
        record = register(db, raw, system["users"]["admin"].id)
        record_id = record.id
        assert register(db, raw, system["users"]["admin"].id).id == record_id
        assert db.scalar(select(func.count()).select_from(EvaluationRecord)) == 1
    client = system["client"]
    path = f"/api/workspaces/{system['workspace']}/evaluations"
    assert client.get(path).status_code == 401
    login(client, "viewer")
    assert len(client.get(path).json()["items"]) == 1
    detail = client.get(f"{path}/{record_id}")
    assert detail.status_code == 200
    assert detail.json()["snapshot"]["strategies"][0]["scores"]["all"]["total"] == 26
    assert "DO_NOT_EXPOSE" not in detail.text
    assert client.get(f"{path}/{uuid.uuid4()}").status_code == 404
    assert client.get(path + "?page=0").status_code == 422
    assert client.get(path + "?page=501").status_code == 422
    with Session(system["engine"]) as db, db.begin():
        db.delete(db.get(Membership, (system["workspace"], system["users"]["viewer"].id)))
    assert client.get(path).status_code == 404
    assert client.get(f"{path}/{record_id}").status_code == 404
    login(client, "other")
    assert client.get(f"/api/workspaces/{system['foreign']}/evaluations").json()["items"] == []
    assert client.get(f"/api/workspaces/{system['foreign']}/evaluations/{record_id}").status_code == 404
    assert client.get(path).status_code == 404


@pytest.mark.parametrize("role,status", [("viewer", 403), ("operator", 403), ("other", 404)])
def test_registration_requires_primary_administrator(system, role, status):
    raw = json.dumps(report(system["workspace"])).encode()
    with Session(system["engine"]) as db, db.begin():
        with pytest.raises(HTTPException) as error:
            register(db, raw, system["users"][role].id)
        assert error.value.status_code == status
        assert db.scalar(select(func.count()).select_from(EvaluationRecord)) == 0


@pytest.mark.parametrize("mismatch", ["foreign", "query", "strategy", "missing", "duplicate"])
def test_mismatched_trace_rejects_atomically(system, mismatch):
    data = prepare(system)
    trace_id = uuid.UUID(data["strategies"]["vector"]["cases"][0]["trace"]["id"])
    with Session(system["engine"]) as db, db.begin():
        trace = db.get(RetrievalTrace, trace_id)
        if mismatch == "foreign":
            trace.workspace_id = system["foreign"]
        elif mismatch == "query":
            trace.query = "different request"
        elif mismatch == "strategy":
            trace.strategy = "different strategy"
        elif mismatch == "missing":
            db.delete(trace)
        else:
            data["strategies"]["vector"]["cases"][1]["trace"]["id"] = str(trace_id)
    with Session(system["engine"]) as db, db.begin():
        with pytest.raises(ValueError):
            register(db, json.dumps(data).encode(), system["users"]["admin"].id)
        assert db.scalar(select(func.count()).select_from(EvaluationRecord)) == 0


def test_list_is_bounded_and_does_not_load_case_details(system):
    with Session(system["engine"]) as db, db.begin():
        for index in range(21):
            db.add(
                EvaluationRecord(
                    workspace_id=system["workspace"],
                    registered_by=system["users"]["admin"].id,
                    report_sha256=f"{index:064x}",
                    source_commit="a" * 40,
                    snapshot={"private": "not listed"},
                )
            )
    login(system["client"], "viewer")
    path = f"/api/workspaces/{system['workspace']}/evaluations"
    first = system["client"].get(path).json()
    second = system["client"].get(path + "?page=2").json()
    assert len(first["items"]) == 20 and first["more"]
    assert len(second["items"]) == 1 and not second["more"]
    assert "snapshot" not in json.dumps(first)


def test_registration_cli_in_fresh_process(system, tmp_path):
    data = prepare(system)
    path = tmp_path / "report.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    env = {**os.environ, "ASI_DATABASE_URL": system["engine"].url.render_as_string(hide_password=False)}
    command = [
        sys.executable,
        "-m",
        "app.register_evaluation",
        str(path),
        "--actor-id",
        str(system["users"]["admin"].id),
    ]
    first = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
    assert first.returncode == 0, first.stderr
    second = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
    assert second.returncode == 0, second.stderr
    assert json.loads(first.stdout) == json.loads(second.stdout)
    assert json.loads(first.stdout)["workspace_id"] == str(system["workspace"])
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(EvaluationRecord)) == 1
