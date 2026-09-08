"""Partial folder updates preserve hierarchy unless movement is explicitly requested."""

import pytest
from test_resource_folders import auth_headers, create_folder, create_workspace, login, register


@pytest.mark.parametrize("resource_type", [
    "knowledge_document", "dataset", "agent_config", "evaluation_run",
])
def test_rename_preserves_parent_and_explicit_null_moves_to_root(client, resource_type):
    register(client, "folder-patch@example.test")
    token = login(client, "folder-patch@example.test")
    headers = auth_headers(token)
    workspace = create_workspace(client, token)
    parent = create_folder(client, token, workspace["id"], resource_type, "Parent")
    base = f"/api/v1/workspaces/{workspace['id']}/resource-folders"
    created = client.post(base, headers=headers, json={
        "name": "Child", "resource_type": resource_type, "parent_folder_id": parent["id"],
    })
    assert created.status_code == 201
    child = created.json()
    assert child["parent_folder_id"] == parent["id"]
    path = base + "/" + child["id"]
    renamed = client.patch(path, headers=headers, json={"name": "Renamed"})
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Renamed"
    assert renamed.json()["parent_folder_id"] == parent["id"]
    listed = client.get(base, headers=headers, params={"resource_type": resource_type})
    assert listed.status_code == 200
    assert next(row for row in listed.json() if row["id"] == child["id"])[
        "parent_folder_id"
    ] == parent["id"]
    unchanged = client.patch(path, headers=headers, json={})
    assert unchanged.status_code == 200
    assert unchanged.json()["parent_folder_id"] == parent["id"]
    other_workspace = create_workspace(client, token, "Other workspace")
    foreign = create_folder(client, token, other_workspace["id"], resource_type, "Foreign")
    rejected = client.patch(path, headers=headers, json={
        "name": "Must not persist", "parent_folder_id": foreign["id"],
    })
    assert rejected.status_code == 404
    after = client.get(base, headers=headers, params={"resource_type": resource_type})
    current = next(row for row in after.json() if row["id"] == child["id"])
    assert current["name"] == "Renamed"
    assert current["parent_folder_id"] == parent["id"]
    moved = client.patch(path, headers=headers, json={"parent_folder_id": None})
    assert moved.status_code == 200
    assert moved.json()["parent_folder_id"] is None
    assert moved.json()["name"] == "Renamed"
