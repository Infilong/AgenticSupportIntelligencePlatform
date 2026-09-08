import pytest
from test_resource_folders import auth_headers, create_folder, create_workspace, login, register


@pytest.mark.parametrize("resource_type", [
    "knowledge_document", "dataset", "agent_config", "evaluation_run",
])
def test_descendant_move_is_rejected_without_changing_tree(client, resource_type):
    register(client, "folder-cycle@example.test")
    token = login(client, "folder-cycle@example.test")
    headers = auth_headers(token)
    workspace = create_workspace(client, token)
    root = create_folder(client, token, workspace["id"], resource_type, "Root")
    base = f"/api/v1/workspaces/{workspace['id']}/resource-folders"
    child = client.post(base, headers=headers, json={
        "name": "Child", "resource_type": resource_type, "parent_folder_id": root["id"],
    }).json()
    leaf = client.post(base, headers=headers, json={
        "name": "Leaf", "resource_type": resource_type, "parent_folder_id": child["id"],
    }).json()
    before = client.get(base, headers=headers, params={"resource_type": resource_type}).json()
    for parent in (child, leaf):
        response = client.patch(base + "/" + root["id"], headers=headers, json={
            "name": "Must not persist", "parent_folder_id": parent["id"],
        })
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "resource_folder_invalid"
        assert client.get(base, headers=headers, params={
            "resource_type": resource_type,
        }).json() == before
    # A valid restructuring still works after rejected moves.
    response = client.patch(base + "/" + leaf["id"], headers=headers,
                            json={"parent_folder_id": root["id"]})
    assert response.status_code == 200
    assert response.json()["parent_folder_id"] == root["id"]
