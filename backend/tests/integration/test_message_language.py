import uuid

import pytest

from tests.integration.conftest import login


@pytest.mark.parametrize(
    "question,expected",
    [("删除账户确认", "zh"), ("削除の確認期限は？", "ja"), ("Deletion confirmation?", "en")],
)
def test_auto_language_is_persisted_and_idempotent(system, question, expected):
    client = system["client"]
    headers = {**login(client), "Idempotency-Key": str(uuid.uuid4())}
    path = f"/api/workspaces/{system['workspace']}/messages"
    payload = {"original": question, "language": "auto"}
    created = client.post(path, headers=headers, json=payload)
    assert created.status_code == 202, created.text
    repeated = client.post(path, headers=headers, json=payload)
    assert repeated.json() == created.json()
    run = client.get(f"/api/workspaces/{system['workspace']}/runs/{created.json()['run_id']}")
    assert run.status_code == 200, run.text
    assert run.json()["language"] == expected
