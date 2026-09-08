import json
import os

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.evaluation import EvaluationMode
from app.models.folder import ResourceFolder
from app.models.user import User
from app.services.evaluation_runner import EvaluationRunner
from tests.test_evaluation_authorization_boundary import snapshot
from tests.test_review_transactions import review_database as review_database
from tests.test_workflow_authorization import protected_workflow as protected_workflow


def reject_audit(db, context, instances):
    if any(isinstance(row, AuditLog) and row.action.startswith("evaluation.") for row in db.new):
        raise RuntimeError("synthetic evaluation audit failure")


@pytest.mark.parametrize("operation", ["move", "archive", "delete"])
def test_evaluation_audit_failure_preserves_evidence(
    client, db_session, protected_workflow, operation,
):
    data = protected_workflow
    path = f"{data['base']}/evaluations/{data['evaluation']}"
    method, body, status = "DELETE", None, 204
    if operation == "move":
        folder = client.post(data["base"] + "/resource-folders", headers=data["owner"],
                             json={"name": "Destination", "resource_type": "evaluation_run"})
        assert folder.status_code == 201, folder.text
        method, path, status = "PATCH", path + "/folder", 200
        body = {"folder_id": folder.json()["id"]}
    if operation == "delete":
        assert client.delete(path, headers=data["owner"]).status_code == 204
        path += "/permanent"
    before = snapshot(db_session)
    assert all(before[index] for index in range(6))
    event.listen(db_session, "before_flush", reject_audit)
    try:
        with pytest.raises(RuntimeError, match="synthetic evaluation audit failure"):
            client.request(method, path, headers=data["owner"], json=body)
    finally:
        event.remove(db_session, "before_flush", reject_audit)
        db_session.rollback()
    assert snapshot(db_session) == before
    assert client.request(method, path, headers=data["owner"], json=body).status_code == status
    after = snapshot(db_session)
    assert len(after[-1]) == len(before[-1]) + 1
    assert after[1] != before[1]


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
@pytest.mark.parametrize("operation", ["move", "archive", "delete"])
def test_postgres_evaluation_audit_visibility_and_retry(review_database, operation):
    engine, ids = review_database
    with Session(engine) as db:
        folder = ResourceFolder(workspace_id=ids[0], created_by_user_id=ids[2][0],
                                resource_type="evaluation_run", name="Destination")
        db.add(folder)
        db.commit()
        folder_id = folder.id
        service = EvaluationRunner(db)
        run = service.run_from_jsonl(
            workspace_id=ids[0], name="Atomic evaluation", agent_id=None,
            modes=[EvaluationMode.direct_llm], current_user=db.get(User, ids[2][0]),
            jsonl_cases=json.dumps({"id": "case", "language": "en", "input_message": "Refund?"}),
        )
        run_id = run.id
        if operation == "delete":
            service.archive_run(workspace_id=ids[0], run_id=run_id, actor_user_id=ids[2][0])

    def observe():
        with Session(engine) as observer:
            return snapshot(observer)

    before = observe()
    assert all(before[index] for index in range(6))
    observed = []

    def fail(db, context, instances):
        if any(isinstance(row, AuditLog) for row in db.new):
            observed.append(observe())
            reject_audit(db, context, instances)

    with Session(engine) as db:
        service = EvaluationRunner(db)

        def mutate():
            args = {"workspace_id": ids[0], "run_id": run_id, "actor_user_id": ids[2][0]}
            if operation == "move":
                return service.move_run(**args, folder_id=folder_id)
            if operation == "archive":
                return service.archive_run(**args)
            return service.delete_archived_run(**args)

        event.listen(db, "before_flush", fail)
        try:
            with pytest.raises(RuntimeError, match="synthetic evaluation audit failure"):
                mutate()
        finally:
            event.remove(db, "before_flush", fail)
        assert observed == [before]
        assert observe() == before
        assert db.is_active
        mutate()
    after = observe()
    assert after[1] != before[1]
    old_ids = {row.id for row in before[-1]}
    audit, = [row for row in after[-1] if row.id not in old_ids]
    assert audit.actor_user_id == ids[2][0]
    assert audit.resource_id == str(run_id)
    action = {"move": "moved", "archive": "archived", "delete": "deleted"}[operation]
    assert audit.action == f"evaluation.{action}"
