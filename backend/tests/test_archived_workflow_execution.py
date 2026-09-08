import pytest
from test_workflow_authorization import ledger_counts
from test_workflow_authorization import protected_workflow as protected_workflow

from app.services.retrieval_service import RetrievalService


@pytest.mark.parametrize("actor", ["owner", "viewer", "reviewer"])
def test_archived_search_denied_before_execution_and_restore_recovers(
    client, db_session, monkeypatch, protected_workflow, actor,
):
    data = protected_workflow
    headers = data["owner"] if actor == "owner" else data["actors"][actor]
    base = data["base"]
    payload = {"query": "Refund request", "language": "en"}
    previous = client.post(base + "/retrieval/search", headers=headers, json=payload)
    assert previous.status_code == 200
    trace_id = previous.json()["trace_id"]
    assert client.post(base + "/archive", headers=data["owner"]).status_code == 200
    before = ledger_counts(db_session)

    calls = []
    original = RetrievalService.search

    def observed(*args, **kwargs):
        calls.append(True)
        return original(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(RetrievalService, "search", observed)
        denied = client.post(base + "/retrieval/search", headers=headers, json=payload)
        assert denied.status_code == 409
        assert calls == []
        assert denied.json()["detail"]["code"] == "workspace_archived"
        assert ledger_counts(db_session) == before
        trace = client.get(base + f"/retrieval/traces/{trace_id}", headers=headers)
        assert trace.status_code == 200
        assert trace.json()["id"] == trace_id
    assert client.post(base + "/restore", headers=data["owner"]).status_code == 200
    restored = client.post(base + "/retrieval/search", headers=headers, json=payload)
    assert restored.status_code == 200
    assert restored.json()["trace_id"] != trace_id
