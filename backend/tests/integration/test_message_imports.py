import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.jobs.models import Job
from app.modules.conversations.models import MessageImport
from app.modules.conversations.service import import_messages, start
from app.modules.support.models import Message, SupportRun
from app.modules.usage.models import ModelCall
from app.modules.workspaces.models import Membership
from tests.integration.conftest import login
from tests.integration.support_helpers import prepare, run_support


def upload(system, data=None, key="import-1", role="operator"):
    client = system["client"]
    auth = login(client, role)
    rows = (
        data
        if data is not None
        else "\n".join(
            json.dumps(row, ensure_ascii=False)
            for row in [
                {
                    "original": " What is the refund deadline? ",
                    "language": "en",
                    "labels": ["Billing", "billing"],
                },
                {"original": "返金期限はいつですか？", "language": "ja", "labels": ["返金"]},
                {"original": "退款期限是什么？", "language": "zh"},
            ]
        )
    )
    return client.post(
        f"/api/workspaces/{system['workspace']}/message-imports",
        headers={**auth, "Idempotency-Key": key},
        files={"file": ("customers.jsonl", rows.encode(), "application/jsonl")},
    )


def test_import_is_saved_customer_data_then_one_selected_message_runs(system):
    prepare(system)
    response = upload(system)
    assert response.status_code == 201, response.text
    assert upload(system).json() == response.json()
    client, ws = system["client"], system["workspace"]
    path = f"/api/workspaces/{ws}/messages"
    page = client.get(path, params={"view": "unprocessed"}).json()
    assert page["total"] == 3
    assert all(row["run_id"] is None and row["state"] == "not_processed" for row in page["items"])
    assert client.get(path).json()["total"] == 3
    assert client.get(path, params={"view": "processing"}).json()["total"] == 0
    chosen = client.get(path, params={"label": "BILLING", "search": "refund"}).json()["items"][0]
    assert chosen["labels"] == ["billing"] and chosen["original"].startswith(" ")
    assert len(client.get(path, params={"limit": 1, "offset": 1}).json()["items"]) == 1
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(SupportRun)) == 0
        assert db.scalar(select(func.count()).select_from(Job).where(Job.kind == "support_run")) == 0
    auth = login(client, "operator")
    detail_path = path + "/" + chosen["id"]
    assert client.get(detail_path).json()["import_filename"] == "customers.jsonl"
    assert client.put(detail_path + "/labels", headers=auth, json={"labels": ["Priority", "返金"]}).json()[
        "labels"
    ] == ["priority", "返金"]
    started = client.post(detail_path + "/process", headers=auth)
    assert started.status_code == 202, started.text
    assert client.post(detail_path + "/process", headers=auth).json() == started.json()
    assert client.get(path, params={"view": "unprocessed"}).json()["total"] == 2
    assert run_support(system)
    detail = client.get(f"/api/workspaces/{ws}/runs/{started.json()['run_id']}").json()
    assert detail["state"] == "waiting_for_input" and detail["retrieval_id"]
    assert detail["original"] == chosen["original"]
    assert "priority" not in detail["input_text"]


@pytest.mark.parametrize(
    "data,status",
    [
        ('{"original":"valid","language":"en"}\n{"original":"secret customer body","language":"fr"}', 422),
        ('{"original":"one","original":"two","language":"en"}', 422),
        ('{"original":"hello","language":"en","labels":["bad,label"]}', 422),
        ("\n", 422),
        ("x" * (1024 * 1024 + 1), 413),
        ("\n".join(['{"original":"hello","language":"en"}'] * 101), 422),
    ],
    ids=["invalid-middle", "duplicate-key", "invalid-label", "empty", "over-bytes", "over-rows"],
)
def test_invalid_import_is_atomic_and_errors_do_not_echo_content(system, data, status):
    result = upload(system, data)
    assert result.status_code == status, result.text
    assert "secret customer body" not in result.text
    with Session(system["engine"]) as db:
        for model in (MessageImport, Message, SupportRun, Job, ModelCall):
            assert db.scalar(select(func.count()).select_from(model)) == 0


def test_import_permissions_conflicts_and_revocation(system):
    assert upload(system).status_code == 201
    assert upload(system, '{"original":"changed","language":"en"}').status_code == 409
    client, ws = system["client"], system["workspace"]
    chosen = client.get(f"/api/workspaces/{ws}/messages").json()["items"][0]
    path = f"/api/workspaces/{ws}/messages/{chosen['id']}"
    assert upload(system, role="viewer").status_code == 403
    for role, denial in [("viewer", 403), ("other", 404)]:
        auth = login(client, role)
        assert client.get(path).status_code == (200 if role == "viewer" else 404)
        assert client.post(path + "/process", headers=auth).status_code == denial
        assert client.put(path + "/labels", headers=auth, json={"labels": ["new"]}).status_code == denial
        assert upload(system, role=role).status_code == denial
    auth = login(client)
    with Session(system["engine"]) as db, db.begin():
        db.get(Membership, (ws, system["users"]["operator"].id)).role = "viewer"
    assert client.post(path + "/process", headers=auth).status_code == 403


def test_concurrent_import_and_first_start_are_idempotent(system):
    actor, ws = system["users"]["operator"].id, system["workspace"]

    def admit(_):
        with Session(system["engine"]) as db, db.begin():
            return import_messages(
                db, ws, actor, "same.jsonl", b'{"original":"refund deadline","language":"en"}', "same"
            ).id

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert len(set(pool.map(admit, range(2)))) == 1
    with Session(system["engine"]) as db:
        message = db.scalar(select(Message.id).where(Message.workspace_id == ws))
        assert db.scalar(select(func.count()).select_from(ModelCall)) == 0

    def process(_):
        with Session(system["engine"]) as db, db.begin():
            return start(db, ws, actor, message)["run_id"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert len(set(pool.map(process, range(2)))) == 1
    with Session(system["engine"]) as db:
        for model in (MessageImport, Message, SupportRun, Job):
            assert db.scalar(select(func.count()).select_from(model)) == 1


def test_concurrent_imports_cannot_overfill_workspace_and_replay_at_capacity(system):
    actor, ws = system["users"]["operator"].id, system["workspace"]
    with Session(system["engine"]) as db, db.begin():
        db.execute(
            text("""INSERT INTO support_messages
            (id, workspace_id, actor_id, original, language, submission_key, input_hash)
            SELECT gen_random_uuid(), :ws, :actor, 'Synthetic stored message', 'en',
            'capacity-' || n, repeat('0',64) FROM generate_series(1,49999) n"""),
            {"ws": ws, "actor": actor},
        )

    def admit(key):
        try:
            with Session(system["engine"]) as db, db.begin():
                batch = import_messages(
                    db, ws, actor, "one.jsonl", b'{"original":"refund deadline","language":"en"}', key
                )
                return key, batch.id
        except HTTPException as error:
            return key, error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(admit, ["one", "two"]))
    assert sum(value == 409 for _, value in results) == 1
    winner = next((key, value) for key, value in results if value != 409)
    assert admit(winner[0]) == winner
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(Message)) == 50000
        assert db.scalar(select(func.count()).select_from(MessageImport)) == 1
        assert db.scalar(select(func.count()).select_from(Job)) == 0
