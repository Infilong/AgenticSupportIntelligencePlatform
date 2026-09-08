"""Real permission dependencies must reject before dataset content or mutations enter services."""

from uuid import UUID

import pytest
from test_dataset_audit_atomicity import CONTENT, snapshot
from test_datasets import auth_headers, create_workspace, login, register

from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.services.dataset_service import DatasetService


@pytest.mark.parametrize("actor,status,operations", [
    ("anonymous", 401, ("list", "examples", "import", "label", "move", "delete")),
    ("outsider", 404, ("list", "examples", "import", "label", "move", "delete")),
    ("reviewer", 403, ("list", "examples", "import", "label", "move", "delete")),
    ("viewer", 403, ("import", "label", "move", "delete")),
    ("member", 403, ("move", "delete")),
    ("developer", 403, ("delete",)),
])
def test_dataset_denial_precedes_service_and_preserves_data(
    client, db_session, monkeypatch, actor, status, operations,
):
    register(client, "dataset-boundary-owner@example.test")
    owner = login(client, "dataset-boundary-owner@example.test")
    workspace = create_workspace(client, owner)
    base = f"/api/v1/workspaces/{workspace['id']}"
    payload = {"dataset_name": "Protected", "source_type": "jsonl", "content": CONTENT}
    imported = client.post(base + "/datasets/import", headers=auth_headers(owner), json=payload)
    assert imported.status_code == 201
    dataset = imported.json()["dataset"]["id"]
    example_path = f"{base}/datasets/{dataset}/examples"
    positive = client.get(example_path, headers=auth_headers(owner))
    assert positive.status_code == 200
    example, = positive.json()
    assert example["messages"] and example["labels"]
    label_path = f"{base}/examples/{example['id']}/labels"
    assert client.post(label_path, headers=auth_headers(owner), json={
        "label_type": "intent", "value": "verified_refund",
    }).status_code == 200

    headers = {}
    if actor != "anonymous":
        user = register(client, "dataset-boundary-reader@example.test")
        headers = auth_headers(login(client, "dataset-boundary-reader@example.test"))
        if actor != "outsider":
            db_session.add(WorkspaceMember(
                workspace_id=UUID(workspace["id"]), user_id=UUID(user["id"]),
                role=WorkspaceRole(actor),
            ))
            db_session.commit()
        if actor in ("viewer", "member", "developer"):
            permitted = client.get(example_path, headers=headers)
            assert permitted.status_code == 200
            assert permitted.json()[0]["messages"]

    before = snapshot(db_session)
    entered = []
    for name in ("list_datasets", "count_datasets", "list_examples", "import_dataset",
                 "upsert_human_label", "move_dataset", "delete_dataset"):
        original = getattr(DatasetService, name)

        def observe(self, _name=name, _original=original, **kwargs):
            entered.append(_name)
            return _original(self, **kwargs)

        monkeypatch.setattr(DatasetService, name, observe)

    requests = {
        "list": ("GET", base + "/datasets", None),
        "examples": ("GET", example_path, None),
        "import": ("POST", base + "/datasets/import", payload),
        "label": ("POST", label_path, {"label_type": "intent", "value": "forbidden"}),
        "move": ("PATCH", f"{base}/datasets/{dataset}/folder", {"folder_id": None}),
        "delete": ("DELETE", f"{base}/datasets/{dataset}", None),
    }
    for operation in operations:
        method, path, body = requests[operation]
        response = client.request(method, path, headers=headers, json=body)
        assert response.status_code == status, response.text
        assert entered == []
        assert snapshot(db_session) == before
