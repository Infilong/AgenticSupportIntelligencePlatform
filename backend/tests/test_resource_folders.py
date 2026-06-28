import json
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.workspace import WorkspaceMember, WorkspaceRole


def register(client: TestClient, email: str, password: str = "strong-password") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "Test User"},
    )
    assert response.status_code == 201
    return response.json()


def login(client: TestClient, email: str, password: str = "strong-password") -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_workspace(client: TestClient, token: str, name: str = "Support Workspace") -> dict:
    response = client.post("/api/v1/workspaces", json={"name": name}, headers=auth_headers(token))
    assert response.status_code == 201
    return response.json()


def jsonl_content(*rows: dict) -> str:
    return "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)


def create_folder(
    client: TestClient, token: str, workspace_id: str, resource_type: str, name: str
) -> dict:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/resource-folders",
        headers=auth_headers(token),
        json={"resource_type": resource_type, "name": name},
    )
    assert response.status_code == 201
    return response.json()


def upload_document(
    client: TestClient, token: str, workspace_id: str, folder_id: str | None = None
) -> dict:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/knowledge-documents",
        headers=auth_headers(token),
        json={
            "title": "Refund Policy",
            "content_type": "text/plain",
            "language": "en",
            "folder_id": folder_id,
            "content": "Refunds are available within 30 days. " * 40,
        },
    )
    assert response.status_code == 201
    return response.json()["document"]


def import_dataset(
    client: TestClient, token: str, workspace_id: str, folder_id: str | None = None
) -> dict:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/datasets/import",
        headers=auth_headers(token),
        json={
            "dataset_name": "Support Examples",
            "source_type": "jsonl",
            "folder_id": folder_id,
            "content": jsonl_content(
                {"messages": [{"role": "user", "content": "Can I get a refund?"}]}
            ),
        },
    )
    assert response.status_code == 201
    return response.json()["dataset"]


def create_agent(
    client: TestClient, token: str, workspace_id: str, folder_id: str | None = None
) -> dict:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/agents",
        headers=auth_headers(token),
        json={"name": "Support Agent", "token_budget": 4000, "folder_id": folder_id},
    )
    assert response.status_code == 201
    return response.json()


def add_member(
    db_session: Session,
    *,
    workspace_id: str,
    user_email: str,
    role: WorkspaceRole = WorkspaceRole.member,
) -> None:
    user = db_session.scalar(select(User).where(User.email == user_email))
    assert user is not None
    db_session.add(
        WorkspaceMember(
            workspace_id=UUID(workspace_id),
            user_id=user.id,
            role=role,
        )
    )
    db_session.commit()


def test_owner_can_organize_filter_move_and_delete_data_resources(client: TestClient) -> None:
    register(client, "folder-owner@example.com")
    token = login(client, "folder-owner@example.com")
    workspace = create_workspace(client, token)

    knowledge_folder = create_folder(
        client, token, workspace["id"], "knowledge_document", "Policies"
    )
    dataset_folder = create_folder(client, token, workspace["id"], "dataset", "Training data")
    document = upload_document(client, token, workspace["id"], knowledge_folder["id"])
    dataset = import_dataset(client, token, workspace["id"], dataset_folder["id"])

    filtered_documents = client.get(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents",
        headers=auth_headers(token),
        params={"folder_id": knowledge_folder["id"]},
    )
    filtered_datasets = client.get(
        f"/api/v1/workspaces/{workspace['id']}/datasets",
        headers=auth_headers(token),
        params={"folder_id": dataset_folder["id"]},
    )

    assert filtered_documents.status_code == 200
    assert [item["id"] for item in filtered_documents.json()] == [document["id"]]
    assert filtered_datasets.status_code == 200
    assert [item["id"] for item in filtered_datasets.json()] == [dataset["id"]]

    reindexed_document = client.post(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents/{document['id']}/reindex",
        headers=auth_headers(token),
        json={
            "title": "Refund Policy Updated",
            "content_type": "text/plain",
            "language": "en",
            "folder_id": None,
            "content": "Refunds are available within 30 days after purchase. " * 40,
        },
    )
    assert reindexed_document.status_code == 200
    assert reindexed_document.json()["document"]["folder_id"] is None

    moved_document = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents/{document['id']}/folder",
        headers=auth_headers(token),
        json={"folder_id": None},
    )
    moved_dataset = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/datasets/{dataset['id']}/folder",
        headers=auth_headers(token),
        json={"folder_id": None},
    )

    assert moved_document.status_code == 200
    assert moved_document.json()["folder_id"] is None
    assert moved_dataset.status_code == 200
    assert moved_dataset.json()["folder_id"] is None

    delete_document = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents/{document['id']}",
        headers=auth_headers(token),
    )
    delete_dataset = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/datasets/{dataset['id']}",
        headers=auth_headers(token),
    )
    delete_knowledge_folder = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/resource-folders/{knowledge_folder['id']}",
        headers=auth_headers(token),
    )
    delete_dataset_folder = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/resource-folders/{dataset_folder['id']}",
        headers=auth_headers(token),
    )

    assert delete_document.status_code == 204
    assert delete_dataset.status_code == 204
    assert delete_knowledge_folder.status_code == 204
    assert delete_dataset_folder.status_code == 204


def test_owner_can_organize_filter_move_and_archive_agent_configs(client: TestClient) -> None:
    register(client, "agent-folder-owner@example.com")
    token = login(client, "agent-folder-owner@example.com")
    workspace = create_workspace(client, token)
    folder = create_folder(client, token, workspace["id"], "agent_config", "Production agents")
    agent = create_agent(client, token, workspace["id"], folder["id"])
    unfiled_agent = create_agent(client, token, workspace["id"])

    filtered_agents = client.get(
        f"/api/v1/workspaces/{workspace['id']}/agents",
        headers=auth_headers(token),
        params={"folder_id": folder["id"]},
    )
    unfiled_agents = client.get(
        f"/api/v1/workspaces/{workspace['id']}/agents",
        headers=auth_headers(token),
    )
    delete_non_empty = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/resource-folders/{folder['id']}",
        headers=auth_headers(token),
    )
    moved_agent = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/agents/{agent['id']}/folder",
        headers=auth_headers(token),
        json={"folder_id": None},
    )
    archive_agent = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/agents/{unfiled_agent['id']}",
        headers=auth_headers(token),
    )
    delete_empty = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/resource-folders/{folder['id']}",
        headers=auth_headers(token),
    )

    assert filtered_agents.status_code == 200
    assert [item["id"] for item in filtered_agents.json()] == [agent["id"]]
    assert unfiled_agents.status_code == 200
    assert {item["id"] for item in unfiled_agents.json()} == {agent["id"], unfiled_agent["id"]}
    assert agent["folder_id"] == folder["id"]
    assert delete_non_empty.status_code == 409
    assert delete_non_empty.json()["detail"]["code"] == "resource_folder_not_empty"
    assert moved_agent.status_code == 200
    assert moved_agent.json()["folder_id"] is None
    assert archive_agent.status_code == 204
    assert delete_empty.status_code == 204


def test_owner_can_rename_folder_and_cannot_delete_non_empty_folder(client: TestClient) -> None:
    register(client, "folder-rename-owner@example.com")
    token = login(client, "folder-rename-owner@example.com")
    workspace = create_workspace(client, token)
    folder = create_folder(client, token, workspace["id"], "knowledge_document", "Old Policies")
    document = upload_document(client, token, workspace["id"], folder["id"])

    renamed = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/resource-folders/{folder['id']}",
        headers=auth_headers(token),
        json={"name": "Regional Policies", "parent_folder_id": None},
    )
    delete_non_empty = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/resource-folders/{folder['id']}",
        headers=auth_headers(token),
    )
    moved_document = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents/{document['id']}/folder",
        headers=auth_headers(token),
        json={"folder_id": None},
    )
    delete_empty = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/resource-folders/{folder['id']}",
        headers=auth_headers(token),
    )

    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Regional Policies"
    assert delete_non_empty.status_code == 409
    assert delete_non_empty.json()["detail"]["code"] == "resource_folder_not_empty"
    assert moved_document.status_code == 200
    assert delete_empty.status_code == 204


def test_folder_and_resource_destructive_actions_require_owner(
    client: TestClient, db_session: Session
) -> None:
    register(client, "owner-rbac@example.com")
    owner_token = login(client, "owner-rbac@example.com")
    workspace = create_workspace(client, owner_token)
    knowledge_folder = create_folder(
        client, owner_token, workspace["id"], "knowledge_document", "Policies"
    )
    document = upload_document(client, owner_token, workspace["id"], knowledge_folder["id"])
    dataset = import_dataset(client, owner_token, workspace["id"])
    agent_folder = create_folder(client, owner_token, workspace["id"], "agent_config", "Agents")
    agent = create_agent(client, owner_token, workspace["id"], agent_folder["id"])

    register(client, "member-rbac@example.com")
    member_token = login(client, "member-rbac@example.com")
    add_member(
        db_session,
        workspace_id=workspace["id"],
        user_email="member-rbac@example.com",
        role=WorkspaceRole.viewer,
    )

    member_list = client.get(
        f"/api/v1/workspaces/{workspace['id']}/resource-folders",
        headers=auth_headers(member_token),
        params={"resource_type": "knowledge_document"},
    )
    folder_delete = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/resource-folders/{knowledge_folder['id']}",
        headers=auth_headers(member_token),
    )
    document_move = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents/{document['id']}/folder",
        headers=auth_headers(member_token),
        json={"folder_id": None},
    )
    document_delete = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents/{document['id']}",
        headers=auth_headers(member_token),
    )
    dataset_delete = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/datasets/{dataset['id']}",
        headers=auth_headers(member_token),
    )
    agent_move = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/agents/{agent['id']}/folder",
        headers=auth_headers(member_token),
        json={"folder_id": None},
    )

    assert member_list.status_code == 200
    assert folder_delete.status_code == 403
    assert document_move.status_code == 403
    assert document_delete.status_code == 403
    assert dataset_delete.status_code == 403
    assert agent_move.status_code == 403
    assert folder_delete.json()["detail"]["code"] == "workspace_permission_required"
    assert folder_delete.json()["detail"]["required_permission"] == "resource_folders:manage"
    assert document_move.json()["detail"]["required_permission"] == "resource_folders:manage"
    assert document_delete.json()["detail"]["required_permission"] == "resources:delete"
    assert dataset_delete.json()["detail"]["required_permission"] == "resources:delete"
    assert agent_move.json()["detail"]["required_permission"] == "resource_folders:manage"


def test_cross_workspace_folder_ids_are_rejected(client: TestClient) -> None:
    register(client, "folder-owner-a@example.com")
    token_a = login(client, "folder-owner-a@example.com")
    workspace_a = create_workspace(client, token_a, "Workspace A")
    foreign_folder = create_folder(client, token_a, workspace_a["id"], "knowledge_document", "A")
    foreign_agent_folder = create_folder(
        client, token_a, workspace_a["id"], "agent_config", "Agents A"
    )

    register(client, "folder-owner-b@example.com")
    token_b = login(client, "folder-owner-b@example.com")
    workspace_b = create_workspace(client, token_b, "Workspace B")

    document_response = client.post(
        f"/api/v1/workspaces/{workspace_b['id']}/knowledge-documents",
        headers=auth_headers(token_b),
        json={
            "title": "Foreign folder attempt",
            "content_type": "text/plain",
            "language": "en",
            "folder_id": foreign_folder["id"],
            "content": "Refunds are available within 30 days. " * 40,
        },
    )
    dataset_response = client.post(
        f"/api/v1/workspaces/{workspace_b['id']}/datasets/import",
        headers=auth_headers(token_b),
        json={
            "dataset_name": "Foreign folder attempt",
            "source_type": "jsonl",
            "folder_id": foreign_folder["id"],
            "content": jsonl_content(
                {"messages": [{"role": "user", "content": "Can I get a refund?"}]}
            ),
        },
    )

    agent_response = client.post(
        f"/api/v1/workspaces/{workspace_b['id']}/agents",
        headers=auth_headers(token_b),
        json={
            "name": "Foreign folder attempt",
            "token_budget": 4000,
            "folder_id": foreign_agent_folder["id"],
        },
    )

    assert document_response.status_code == 404
    assert document_response.json()["detail"]["code"] == "resource_folder_not_found"
    assert dataset_response.status_code == 404
    assert dataset_response.json()["detail"]["code"] == "resource_folder_not_found"
    assert agent_response.status_code == 404
    assert agent_response.json()["detail"]["code"] == "resource_folder_not_found"
