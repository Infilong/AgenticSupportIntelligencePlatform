import json
from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy import select

from app.models.ai import AIRun, AIRunStatus
from app.models.audit import AuditLog
from app.models.workspace import Workspace, WorkspaceRole
from tests.test_agents import (
    add_workspace_member,
    auth_headers,
    create_workspace,
    login,
    register,
)


@pytest.fixture
def attempts(client, db_session):
    register(client, "billing-owner@example.test")
    owner = auth_headers(login(client, "billing-owner@example.test"))
    workspace = create_workspace(client, owner["Authorization"].split()[1])
    rows = [AIRun(workspace_id=UUID(workspace["id"]), provider="openai",
                  model="text-embedding-3-small", purpose="embedding_query", language="en",
                  status=status, prompt_tokens=100, completion_tokens=0, total_tokens=100,
                  estimated_cost=0.002, latency_ms=15, cache_hit=False,
                  error_message="embedding_usage_unknown_requires_reconciliation")
            for status in (AIRunStatus.uncertain, AIRunStatus.pending)]
    db_session.add_all(rows)
    db_session.commit()
    return f"/api/v1/workspaces/{workspace['id']}/embedding-attempts", owner, rows


@pytest.mark.parametrize("tokens", [0, 7, 150])
def test_reconcile_usage_and_audit_without_fabricating_success(
    client, db_session, attempts, tokens,
):
    base, owner, rows = attempts
    path = f"{base}/{rows[0].id}/reconcile"
    response = client.post(path, headers=owner, json={
        "confirmed_tokens": tokens, "evidence_reference": "billing-case-17"})
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["total_tokens"] == tokens
    assert response.json()["estimated_cost"] == pytest.approx(tokens * 0.00002)
    audit = db_session.scalar(select(AuditLog).where(
        AuditLog.action == "embedding_usage.reconciled"))
    data = json.loads(audit.metadata_json)
    assert audit.actor_user_id is not None
    assert data["previous"]["total_tokens"] == 100
    assert data["previous"]["error_message"] == "embedding_usage_unknown_requires_reconciliation"
    assert data["evidence_reference"] == "billing-case-17"
    assert client.post(path, headers=owner, json={
        "confirmed_tokens": tokens, "evidence_reference": "repeat"}).status_code == 409
    assert len(list(db_session.scalars(select(AuditLog).where(
        AuditLog.action == "embedding_usage.reconciled")))) == 1


@pytest.mark.parametrize("tokens,reference", [(-1, "case"), (True, "case"), (1.5, "case"),
                                            ("2", "case"), (2, " "), (2, "x" * 241)])
def test_invalid_confirmation_is_rejected(client, attempts, tokens, reference):
    base, owner, rows = attempts
    assert client.post(f"{base}/{rows[0].id}/reconcile", headers=owner, json={
        "confirmed_tokens": tokens, "evidence_reference": reference}).status_code == 422
    assert rows[0].status == AIRunStatus.uncertain


def test_pending_cannot_be_reconciled_and_list_is_bounded(client, attempts):
    base, owner, rows = attempts
    first = client.get(base + "?limit=1", headers=owner).json()
    second = client.get(base + "?limit=1&offset=1", headers=owner).json()
    assert first["has_more"] and not second["has_more"]
    assert {first["items"][0]["id"], second["items"][0]["id"]} == {str(row.id) for row in rows}
    assert client.get(base + "?limit=101", headers=owner).status_code == 422
    assert client.post(f"{base}/{rows[1].id}/reconcile", headers=owner, json={
        "confirmed_tokens": 0, "evidence_reference": "case"}).status_code == 409


@pytest.mark.parametrize("operation", ["reconcile", "recover"])
@pytest.mark.parametrize("actor,expected", [("anonymous", 401), ("outsider", 404),
    ("viewer", 403), ("reviewer", 403), ("member", 403), ("developer", 403)])
def test_permission_boundary(client, db_session, attempts, actor, expected, operation):
    base, _, rows = attempts
    headers = {}
    if actor != "anonymous":
        email = f"billing-{actor}@example.test"
        register(client, email)
        headers = auth_headers(login(client, email))
        if actor != "outsider":
            add_workspace_member(db_session, workspace_id=str(rows[0].workspace_id),
                                 user_email=email, role=WorkspaceRole(actor))
    payload = ({"reason": "Investigate"} if operation == "recover" else
               {"confirmed_tokens": 0, "evidence_reference": "case"})
    response = client.post(f"{base}/{rows[0].id}/{operation}", headers=headers, json=payload)
    assert response.status_code == expected
    assert rows[0].status == AIRunStatus.uncertain
    if actor in ("anonymous", "outsider"):
        assert client.get(base, headers=headers).status_code == expected


@pytest.mark.parametrize("operation", ["reconcile", "recover"])
def test_foreign_attempt_not_visible_in_owned_workspace(client, attempts, operation):
    _, owner, rows = attempts
    workspace = create_workspace(client, owner["Authorization"].split()[1], "Other")
    base = f"/api/v1/workspaces/{workspace['id']}/embedding-attempts"
    assert client.get(base, headers=owner).json()["items"] == []
    payload = ({"reason": "Investigate"} if operation == "recover" else
               {"confirmed_tokens": 0, "evidence_reference": "case"})
    assert client.post(f"{base}/{rows[0].id}/{operation}", headers=owner,
                       json=payload).status_code == 404


@pytest.mark.parametrize("operation", ["reconcile", "recover"])
def test_archived_workspace_rejects_reconciliation(client, db_session, attempts, operation):
    base, owner, rows = attempts
    workspace = db_session.get(Workspace, rows[0].workspace_id)
    workspace.archived_at = datetime.now(UTC)
    db_session.commit()
    payload = ({"reason": "Investigate"} if operation == "recover" else
               {"confirmed_tokens": 0, "evidence_reference": "case"})
    assert client.post(f"{base}/{rows[0].id}/{operation}", headers=owner,
                       json=payload).status_code == 409
    assert rows[0].status == AIRunStatus.uncertain


def test_nonembedding_calls_cannot_be_reconciled(client, db_session, attempts):
    base, owner, rows = attempts
    rows[0].purpose = "draft"
    db_session.commit()
    assert client.post(f"{base}/{rows[0].id}/reconcile", headers=owner, json={
        "confirmed_tokens": 0, "evidence_reference": "case"}).status_code == 404
