"""Evaluation management denial must precede service access and preserve stored evidence."""

import pytest
from sqlalchemy import select

from app.models.ai import AIRun
from app.models.audit import AuditLog
from app.models.evaluation import EvaluationCase, EvaluationMetric, EvaluationResult, EvaluationRun
from app.models.reservation import ModelCallReservation
from app.models.workspace import WorkspaceRole
from app.services.evaluation_runner import EvaluationRunner
from tests.test_agents import add_workspace_member, auth_headers, login, register
from tests.test_workflow_authorization import protected_workflow as protected_workflow


def snapshot(db):
    db.expire_all()
    return [db.execute(select(*model.__table__.c).order_by(model.id)).all() for model in (
        EvaluationCase, EvaluationRun, EvaluationResult, EvaluationMetric,
        AIRun, ModelCallReservation, AuditLog,
    )]


@pytest.mark.parametrize("actor,status,operations", [
    ("anonymous", 401, ("list", "detail", "compare", "move", "archive", "delete")),
    ("outsider", 404, ("list", "detail", "compare", "move", "archive", "delete")),
    ("reviewer", 403, ("list", "detail", "compare", "move", "archive", "delete")),
    ("viewer", 403, ("move", "archive", "delete")),
    ("member", 403, ("move", "archive", "delete")),
    ("developer", 403, ("archive", "delete")),
])
def test_evaluation_denial_precedes_service_and_preserves_evidence(
    client, db_session, monkeypatch, protected_workflow, actor, status, operations,
):
    data = protected_workflow
    base = data["base"] + "/evaluations"
    current = data["evaluation"]
    baseline = client.post(base, headers=data["owner"], json=data["evaluation_payload"])
    assert baseline.status_code == 201
    archived = baseline.json()["run"]["id"]
    assert baseline.json()["results"] and baseline.json()["metrics"]
    assert client.delete(f"{base}/{archived}", headers=data["owner"]).status_code == 204
    if actor == "member":
        email = "evaluation-member@example.test"
        register(client, email)
        data["actors"][actor] = auth_headers(login(client, email))
        add_workspace_member(db_session, workspace_id=data["base"].split("/")[-1],
                             user_email=email, role=WorkspaceRole.member)
    headers = data["actors"][actor]
    requests = {
        "list": ("GET", base + "?include_archived=true", None),
        "detail": ("GET", f"{base}/{current}", None),
        "compare": ("GET", f"{base}/{current}/compare/{archived}", None),
        "move": ("PATCH", f"{base}/{current}/folder", {"folder_id": None}),
        "archive": ("DELETE", f"{base}/{current}", None),
        "delete": ("DELETE", f"{base}/{archived}/permanent", None),
    }
    # Existing populated and archived runs make these real resource checks, not missing IDs.
    for operation in ("list", "detail", "compare"):
        _, path, _ = requests[operation]
        allowed = headers if actor in ("viewer", "member", "developer") else data["owner"]
        response = client.get(path, headers=allowed)
        assert response.status_code == 200, response.text
        assert "PRIVATE-EVAL-SENTINEL" in response.text

    before = snapshot(db_session)
    entered = []
    for name in ("list_runs", "get_run_detail", "compare_runs", "move_run",
                 "archive_run", "delete_archived_run"):
        original = getattr(EvaluationRunner, name)

        def observe(self, _name=name, _original=original, **kwargs):
            entered.append(_name)
            return _original(self, **kwargs)

        monkeypatch.setattr(EvaluationRunner, name, observe)
    for operation in operations:
        method, path, payload = requests[operation]
        response = client.request(method, path, headers=headers, json=payload)
        assert response.status_code == status, response.text
        assert "SENTINEL" not in response.text
        assert current not in response.text and archived not in response.text
        assert entered == []
        assert snapshot(db_session) == before
