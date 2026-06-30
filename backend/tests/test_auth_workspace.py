from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token, hash_password, verify_password
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
    body = response.json()
    assert body["token_type"] == "bearer"
    return body["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def add_workspace_member(
    db_session: Session, *, workspace_id: str, user_email: str, role: WorkspaceRole
) -> None:
    user = db_session.query(User).filter_by(email=user_email).one()
    db_session.add(
        WorkspaceMember(workspace_id=UUID(workspace_id), user_id=user.id, role=role)
    )
    db_session.commit()


def test_password_hashing_verifies_password_and_rejects_wrong_password() -> None:
    password_hash = hash_password("strong-password")

    assert password_hash != "strong-password"
    assert verify_password("strong-password", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_register_normalizes_email_and_rejects_duplicate(
    client: TestClient, db_session: Session
) -> None:
    body = register(client, "Engineer@Example.COM")

    assert body["email"] == "engineer@example.com"
    stored_user = db_session.query(User).filter_by(email="engineer@example.com").one()
    assert stored_user.password_hash != "strong-password"

    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "email": "engineer@example.com",
            "password": "another-password",
            "display_name": "Duplicate",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "email_already_registered"


def test_login_returns_token_with_user_subject(client: TestClient) -> None:
    user = register(client, "engineer@example.com")

    token = login(client, "ENGINEER@example.com")

    assert decode_access_token(token, get_settings()) == user["id"]


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    register(client, "engineer@example.com")

    response = client.post(
        "/api/v1/auth/login", json={"email": "engineer@example.com", "password": "wrong"}
    )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_credentials"


def test_workspace_routes_reject_missing_or_invalid_token(client: TestClient) -> None:
    missing = client.get("/api/v1/workspaces")
    invalid = client.get("/api/v1/workspaces", headers=auth_headers("not-a-token"))

    assert missing.status_code == 401
    assert missing.json()["detail"]["code"] == "not_authenticated"
    assert invalid.status_code == 401
    assert invalid.json()["detail"]["code"] == "invalid_token"


def test_user_can_create_list_and_read_own_workspace(client: TestClient) -> None:
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")

    create_response = client.post(
        "/api/v1/workspaces", json={"name": "Japan Support"}, headers=auth_headers(token)
    )
    assert create_response.status_code == 201
    workspace = create_response.json()
    assert workspace["name"] == "Japan Support"

    list_response = client.get("/api/v1/workspaces", headers=auth_headers(token))
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [workspace["id"]]

    detail_response = client.get(
        f"/api/v1/workspaces/{workspace['id']}", headers=auth_headers(token)
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == workspace["id"]


def test_user_cannot_access_another_users_workspace(client: TestClient) -> None:
    register(client, "owner@example.com")
    owner_token = login(client, "owner@example.com")
    workspace_response = client.post(
        "/api/v1/workspaces", json={"name": "Private Workspace"}, headers=auth_headers(owner_token)
    )
    workspace_id = workspace_response.json()["id"]

    register(client, "other@example.com")
    other_token = login(client, "other@example.com")

    forbidden_detail = client.get(
        f"/api/v1/workspaces/{workspace_id}", headers=auth_headers(other_token)
    )
    other_list = client.get("/api/v1/workspaces", headers=auth_headers(other_token))

    assert forbidden_detail.status_code == 404
    assert forbidden_detail.json()["detail"]["code"] == "workspace_not_found"
    assert other_list.status_code == 200
    assert other_list.json() == []


def test_malformed_workspace_id_returns_controlled_error(client: TestClient) -> None:
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")

    response = client.get("/api/v1/workspaces/not-a-uuid", headers=auth_headers(token))

    assert response.status_code == 422


def test_workspace_create_rejects_blank_name(client: TestClient) -> None:
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")

    response = client.post("/api/v1/workspaces", json={"name": "   "}, headers=auth_headers(token))

    assert response.status_code == 422


def test_workspace_create_rejects_duplicate_visible_name(client: TestClient) -> None:
    register(client, "duplicate-workspace-owner@example.com")
    token = login(client, "duplicate-workspace-owner@example.com")

    first = client.post(
        "/api/v1/workspaces", json={"name": "Japan Support"}, headers=auth_headers(token)
    )
    duplicate = client.post(
        "/api/v1/workspaces", json={"name": "  japan support  "}, headers=auth_headers(token)
    )
    workspaces = client.get("/api/v1/workspaces", headers=auth_headers(token))

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "workspace_name_conflict"
    assert [workspace["name"] for workspace in workspaces.json()] == ["Japan Support"]


def test_different_users_can_use_same_workspace_name(client: TestClient) -> None:
    register(client, "same-name-owner-a@example.com")
    token_a = login(client, "same-name-owner-a@example.com")
    register(client, "same-name-owner-b@example.com")
    token_b = login(client, "same-name-owner-b@example.com")

    response_a = client.post(
        "/api/v1/workspaces", json={"name": "Shared Label"}, headers=auth_headers(token_a)
    )
    response_b = client.post(
        "/api/v1/workspaces", json={"name": "Shared Label"}, headers=auth_headers(token_b)
    )

    assert response_a.status_code == 201
    assert response_b.status_code == 201


def test_workspace_membership_endpoint_returns_owner_permissions(client: TestClient) -> None:
    register(client, "owner-permissions@example.com")
    token = login(client, "owner-permissions@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Permission Workspace"},
        headers=auth_headers(token),
    ).json()

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/membership",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["workspace_id"] == workspace["id"]
    assert body["role"] == "owner"
    assert body["can_manage_resources"] is True
    assert body["can_manage_workspace"] is True
    assert "settings:read" in body["permissions"]
    assert "prompts:write" in body["permissions"]
    assert "models:write" in body["permissions"]
    assert "tools:configure" in body["permissions"]
    assert "guardrails:configure" in body["permissions"]
    assert "resources:delete" in body["permissions"]
    assert "resource_folders:manage" in body["permissions"]


def test_workspace_membership_endpoint_returns_viewer_permissions(
    client: TestClient, db_session: Session
) -> None:
    register(client, "owner-viewer-permissions@example.com")
    owner_token = login(client, "owner-viewer-permissions@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Viewer Permission Workspace"},
        headers=auth_headers(owner_token),
    ).json()

    register(client, "plain-viewer@example.com")
    viewer_token = login(client, "plain-viewer@example.com")
    add_workspace_member(
        db_session,
        workspace_id=workspace["id"],
        user_email="plain-viewer@example.com",
        role=WorkspaceRole.viewer,
    )

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/membership",
        headers=auth_headers(viewer_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "viewer"
    assert body["can_manage_resources"] is False
    assert body["can_manage_workspace"] is False
    assert "workspace:read" in body["permissions"]
    assert "tasks:read" in body["permissions"]
    assert "knowledge:read" in body["permissions"]
    assert "agents:read" in body["permissions"]
    assert "traces:read" in body["permissions"]
    assert "reviews:read" in body["permissions"]
    assert "evaluations:read" in body["permissions"]
    assert "costs:read" in body["permissions"]
    assert "settings:read" in body["permissions"]
    assert "tools:read" not in body["permissions"]
    assert "prompts:read" not in body["permissions"]
    assert "models:read" not in body["permissions"]
    assert "data:write" not in body["permissions"]
    assert "agents:run" not in body["permissions"]
    assert "reviews:resolve" not in body["permissions"]
    assert "resources:delete" not in body["permissions"]
    assert "prompts:write" not in body["permissions"]
    assert "models:write" not in body["permissions"]
    assert "tools:configure" not in body["permissions"]


def test_workspace_membership_endpoint_hides_other_workspaces(client: TestClient) -> None:
    register(client, "membership-owner@example.com")
    owner_token = login(client, "membership-owner@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Private Membership Workspace"},
        headers=auth_headers(owner_token),
    ).json()

    register(client, "membership-other@example.com")
    other_token = login(client, "membership-other@example.com")

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/membership",
        headers=auth_headers(other_token),
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "workspace_not_found"


def test_owner_can_list_add_update_and_remove_workspace_members(client: TestClient) -> None:
    owner = register(client, "member-admin-owner@example.com")
    owner_token = login(client, "member-admin-owner@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Member Admin Workspace"},
        headers=auth_headers(owner_token),
    ).json()
    member = register(client, "member-admin-target@example.com")

    add_response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/members",
        headers=auth_headers(owner_token),
        json={"email": "MEMBER-admin-target@example.com", "role": "member"},
    )
    list_response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/members",
        headers=auth_headers(owner_token),
    )
    promote_response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/members/{member['id']}",
        headers=auth_headers(owner_token),
        json={"role": "owner"},
    )
    demote_response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/members/{member['id']}",
        headers=auth_headers(owner_token),
        json={"role": "member"},
    )
    remove_response = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/members/{member['id']}",
        headers=auth_headers(owner_token),
    )
    final_list = client.get(
        f"/api/v1/workspaces/{workspace['id']}/members",
        headers=auth_headers(owner_token),
    )

    assert owner["id"] != member["id"]
    assert add_response.status_code == 201
    assert add_response.json()["email"] == "member-admin-target@example.com"
    assert add_response.json()["role"] == "member"
    assert "workspace:read" in add_response.json()["permissions"]
    assert list_response.status_code == 200
    assert [item["email"] for item in list_response.json()] == [
        "member-admin-owner@example.com",
        "member-admin-target@example.com",
    ]
    assert promote_response.status_code == 200
    assert promote_response.json()["role"] == "owner"
    assert demote_response.status_code == 200
    assert demote_response.json()["role"] == "member"
    assert remove_response.status_code == 204
    assert [item["email"] for item in final_list.json()] == ["member-admin-owner@example.com"]


def test_workspace_member_management_rejects_missing_duplicate_and_non_owner(
    client: TestClient, db_session: Session
) -> None:
    register(client, "member-management-owner@example.com")
    owner_token = login(client, "member-management-owner@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Owner Workspace"},
        headers=auth_headers(owner_token),
    ).json()
    register(client, "member-management-existing@example.com")
    existing_token = login(client, "member-management-existing@example.com")
    add_workspace_member(
        db_session,
        workspace_id=workspace["id"],
        user_email="member-management-existing@example.com",
        role=WorkspaceRole.member,
    )

    missing = client.post(
        f"/api/v1/workspaces/{workspace['id']}/members",
        headers=auth_headers(owner_token),
        json={"email": "missing-member@example.com", "role": "member"},
    )
    duplicate = client.post(
        f"/api/v1/workspaces/{workspace['id']}/members",
        headers=auth_headers(owner_token),
        json={"email": "member-management-existing@example.com", "role": "member"},
    )
    non_owner_add = client.post(
        f"/api/v1/workspaces/{workspace['id']}/members",
        headers=auth_headers(existing_token),
        json={"email": "missing-member@example.com", "role": "member"},
    )

    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "workspace_member_user_not_found"
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "workspace_member_already_exists"
    assert non_owner_add.status_code == 403
    assert non_owner_add.json()["detail"]["code"] == "workspace_owner_required"


def test_workspace_member_management_preserves_owner_membership(
    client: TestClient, db_session: Session
) -> None:
    owner = register(client, "owner-guard@example.com")
    owner_token = login(client, "owner-guard@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Owner Guard Workspace"},
        headers=auth_headers(owner_token),
    ).json()
    other_owner = register(client, "other-owner-guard@example.com")
    add_workspace_member(
        db_session,
        workspace_id=workspace["id"],
        user_email="other-owner-guard@example.com",
        role=WorkspaceRole.owner,
    )

    self_demote = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/members/{owner['id']}",
        headers=auth_headers(owner_token),
        json={"role": "member"},
    )
    self_remove = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/members/{owner['id']}",
        headers=auth_headers(owner_token),
    )
    remove_other_owner = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/members/{other_owner['id']}",
        headers=auth_headers(owner_token),
    )

    assert self_demote.status_code == 409
    assert self_demote.json()["detail"]["code"] == "workspace_owner_guard"
    assert self_remove.status_code == 409
    assert self_remove.json()["detail"]["code"] == "workspace_owner_guard"
    assert remove_other_owner.status_code == 204


def test_workspace_member_list_is_workspace_scoped(client: TestClient) -> None:
    register(client, "scoped-owner@example.com")
    owner_token = login(client, "scoped-owner@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Scoped Workspace"},
        headers=auth_headers(owner_token),
    ).json()
    register(client, "scoped-other@example.com")
    other_token = login(client, "scoped-other@example.com")

    forbidden = client.get(
        f"/api/v1/workspaces/{workspace['id']}/members",
        headers=auth_headers(other_token),
    )

    assert forbidden.status_code == 404
    assert forbidden.json()["detail"]["code"] == "workspace_not_found"


def test_workspace_owner_can_update_workspace_settings(client: TestClient) -> None:
    register(client, "workspace-settings-owner@example.com")
    token = login(client, "workspace-settings-owner@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Original Workspace"},
        headers=auth_headers(token),
    ).json()

    updated = client.patch(
        f"/api/v1/workspaces/{workspace['id']}",
        headers=auth_headers(token),
        json={"name": "Production AI Platform"},
    )
    detail = client.get(
        f"/api/v1/workspaces/{workspace['id']}",
        headers=auth_headers(token),
    )

    assert updated.status_code == 200
    assert updated.json()["name"] == "Production AI Platform"
    assert detail.json()["name"] == "Production AI Platform"


def test_workspace_settings_update_rejects_duplicate_visible_name(client: TestClient) -> None:
    register(client, "workspace-settings-duplicate-owner@example.com")
    token = login(client, "workspace-settings-duplicate-owner@example.com")
    first = client.post(
        "/api/v1/workspaces",
        json={"name": "Support Production"},
        headers=auth_headers(token),
    ).json()
    second = client.post(
        "/api/v1/workspaces",
        json={"name": "Support Sandbox"},
        headers=auth_headers(token),
    ).json()

    duplicate = client.patch(
        f"/api/v1/workspaces/{second['id']}",
        headers=auth_headers(token),
        json={"name": " support production "},
    )
    unchanged = client.get(
        f"/api/v1/workspaces/{second['id']}",
        headers=auth_headers(token),
    )

    assert first["name"] == "Support Production"
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "workspace_name_conflict"
    assert unchanged.json()["name"] == "Support Sandbox"


def test_workspace_settings_update_requires_owner(client: TestClient, db_session: Session) -> None:
    register(client, "workspace-settings-owner-rbac@example.com")
    owner_token = login(client, "workspace-settings-owner-rbac@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Owner Settings Workspace"},
        headers=auth_headers(owner_token),
    ).json()
    register(client, "workspace-settings-member@example.com")
    member_token = login(client, "workspace-settings-member@example.com")
    add_workspace_member(
        db_session,
        workspace_id=workspace["id"],
        user_email="workspace-settings-member@example.com",
        role=WorkspaceRole.member,
    )

    member_update = client.patch(
        f"/api/v1/workspaces/{workspace['id']}",
        headers=auth_headers(member_token),
        json={"name": "Member Rename Attempt"},
    )
    blank_update = client.patch(
        f"/api/v1/workspaces/{workspace['id']}",
        headers=auth_headers(owner_token),
        json={"name": "   "},
    )

    assert member_update.status_code == 403
    assert member_update.json()["detail"]["code"] == "workspace_owner_required"
    assert blank_update.status_code == 422


def test_workspace_settings_update_is_workspace_scoped(client: TestClient) -> None:
    register(client, "workspace-settings-owner-a@example.com")
    token_a = login(client, "workspace-settings-owner-a@example.com")
    workspace_a = client.post(
        "/api/v1/workspaces",
        json={"name": "Workspace A"},
        headers=auth_headers(token_a),
    ).json()
    register(client, "workspace-settings-owner-b@example.com")
    token_b = login(client, "workspace-settings-owner-b@example.com")

    forbidden = client.patch(
        f"/api/v1/workspaces/{workspace_a['id']}",
        headers=auth_headers(token_b),
        json={"name": "Cross Workspace Attempt"},
    )

    assert forbidden.status_code == 404
    assert forbidden.json()["detail"]["code"] == "workspace_not_found"


def test_workspace_role_presets_expose_distinct_permissions(
    client: TestClient, db_session: Session
) -> None:
    register(client, "role-preset-owner@example.com")
    owner_token = login(client, "role-preset-owner@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Role Preset Workspace"},
        headers=auth_headers(owner_token),
    ).json()

    role_users = {
        WorkspaceRole.developer: "role-developer@example.com",
        WorkspaceRole.reviewer: "role-reviewer@example.com",
        WorkspaceRole.viewer: "role-viewer@example.com",
    }
    tokens = {}
    for role, email in role_users.items():
        register(client, email)
        tokens[role] = login(client, email)
        add_workspace_member(
            db_session,
            workspace_id=workspace["id"],
            user_email=email,
            role=role,
        )

    developer = client.get(
        f"/api/v1/workspaces/{workspace['id']}/membership",
        headers=auth_headers(tokens[WorkspaceRole.developer]),
    ).json()
    reviewer = client.get(
        f"/api/v1/workspaces/{workspace['id']}/membership",
        headers=auth_headers(tokens[WorkspaceRole.reviewer]),
    ).json()
    viewer = client.get(
        f"/api/v1/workspaces/{workspace['id']}/membership",
        headers=auth_headers(tokens[WorkspaceRole.viewer]),
    ).json()

    assert developer["role"] == "developer"
    assert "data:write" in developer["permissions"]
    assert "knowledge:write" in developer["permissions"]
    assert "agents:run" in developer["permissions"]
    assert "resource_folders:manage" in developer["permissions"]
    assert "resources:delete" not in developer["permissions"]

    assert reviewer["role"] == "reviewer"
    assert "reviews:resolve" in reviewer["permissions"]
    assert "reviews:read" in reviewer["permissions"]
    assert "data:write" not in reviewer["permissions"]
    assert "agents:run" not in reviewer["permissions"]

    assert viewer["role"] == "viewer"
    assert "workspace:read" in viewer["permissions"]
    assert "reviews:resolve" not in viewer["permissions"]
    assert "data:write" not in viewer["permissions"]



def test_role_scoped_read_permissions_hide_admin_surfaces(
    client: TestClient, db_session: Session
) -> None:
    register(client, "role-read-owner@example.com")
    owner_token = login(client, "role-read-owner@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Role Read Workspace"},
        headers=auth_headers(owner_token),
    ).json()

    register(client, "role-read-developer@example.com")
    developer_token = login(client, "role-read-developer@example.com")
    add_workspace_member(
        db_session,
        workspace_id=workspace["id"],
        user_email="role-read-developer@example.com",
        role=WorkspaceRole.developer,
    )

    register(client, "role-read-reviewer@example.com")
    reviewer_token = login(client, "role-read-reviewer@example.com")
    add_workspace_member(
        db_session,
        workspace_id=workspace["id"],
        user_email="role-read-reviewer@example.com",
        role=WorkspaceRole.reviewer,
    )

    register(client, "role-read-viewer@example.com")
    viewer_token = login(client, "role-read-viewer@example.com")
    add_workspace_member(
        db_session,
        workspace_id=workspace["id"],
        user_email="role-read-viewer@example.com",
        role=WorkspaceRole.viewer,
    )

    developer_members = client.get(
        f"/api/v1/workspaces/{workspace['id']}/members",
        headers=auth_headers(developer_token),
    )
    developer_audit = client.get(
        f"/api/v1/workspaces/{workspace['id']}/audit-logs",
        headers=auth_headers(developer_token),
    )
    developer_prompts = client.get(
        f"/api/v1/workspaces/{workspace['id']}/prompt-templates",
        headers=auth_headers(developer_token),
    )
    reviewer_tools = client.get(
        f"/api/v1/workspaces/{workspace['id']}/tools",
        headers=auth_headers(reviewer_token),
    )
    reviewer_reviews = client.get(
        f"/api/v1/workspaces/{workspace['id']}/human-reviews",
        headers=auth_headers(reviewer_token),
    )
    viewer_models = client.get(
        f"/api/v1/workspaces/{workspace['id']}/model-configs",
        headers=auth_headers(viewer_token),
    )
    viewer_datasets = client.get(
        f"/api/v1/workspaces/{workspace['id']}/datasets",
        headers=auth_headers(viewer_token),
    )
    owner_members = client.get(
        f"/api/v1/workspaces/{workspace['id']}/members",
        headers=auth_headers(owner_token),
    )

    assert developer_members.status_code == 403
    assert developer_members.json()["detail"]["required_permission"] == "members:read"
    assert developer_audit.status_code == 403
    assert developer_audit.json()["detail"]["required_permission"] == "audit:read"
    assert developer_prompts.status_code == 200

    assert reviewer_tools.status_code == 403
    assert reviewer_tools.json()["detail"]["required_permission"] == "tools:read"
    assert reviewer_reviews.status_code == 200

    assert viewer_models.status_code == 403
    assert viewer_models.json()["detail"]["required_permission"] == "models:read"
    assert viewer_datasets.status_code == 200

    assert owner_members.status_code == 200

def test_workspace_permission_dependency_blocks_disallowed_role_actions(
    client: TestClient, db_session: Session
) -> None:
    register(client, "role-gate-owner@example.com")
    owner_token = login(client, "role-gate-owner@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Role Gate Workspace"},
        headers=auth_headers(owner_token),
    ).json()
    agent = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents",
        headers=auth_headers(owner_token),
        json={"name": "Role Gate Agent", "token_budget": 4000},
    ).json()

    register(client, "role-gate-developer@example.com")
    developer_token = login(client, "role-gate-developer@example.com")
    add_workspace_member(
        db_session,
        workspace_id=workspace["id"],
        user_email="role-gate-developer@example.com",
        role=WorkspaceRole.developer,
    )

    register(client, "role-gate-viewer@example.com")
    viewer_token = login(client, "role-gate-viewer@example.com")
    add_workspace_member(
        db_session,
        workspace_id=workspace["id"],
        user_email="role-gate-viewer@example.com",
        role=WorkspaceRole.viewer,
    )

    register(client, "role-gate-reviewer@example.com")
    reviewer_token = login(client, "role-gate-reviewer@example.com")
    add_workspace_member(
        db_session,
        workspace_id=workspace["id"],
        user_email="role-gate-reviewer@example.com",
        role=WorkspaceRole.reviewer,
    )

    viewer_import = client.post(
        f"/api/v1/workspaces/{workspace['id']}/datasets/import",
        headers=auth_headers(viewer_token),
        json={
            "dataset_name": "Viewer Import",
            "source_type": "jsonl",
            "content": '{"messages":[{"role":"user","content":"Can I get a refund?"}]}',
        },
    )
    developer_import = client.post(
        f"/api/v1/workspaces/{workspace['id']}/datasets/import",
        headers=auth_headers(developer_token),
        json={
            "dataset_name": "Developer Import",
            "source_type": "jsonl",
            "content": '{"messages":[{"role":"user","content":"Can I get a refund?"}]}',
        },
    )
    reviewer_run = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents/{agent['id']}/runs",
        headers=auth_headers(reviewer_token),
        json={"input_message": "Can I get a refund?"},
    )
    developer_run = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents/{agent['id']}/runs",
        headers=auth_headers(developer_token),
        json={"input_message": "Can I get a refund?"},
    )

    assert viewer_import.status_code == 403
    assert viewer_import.json()["detail"]["code"] == "workspace_permission_required"
    assert viewer_import.json()["detail"]["required_permission"] == "data:write"
    assert developer_import.status_code == 201

    assert reviewer_run.status_code == 403
    assert reviewer_run.json()["detail"]["required_permission"] == "agents:run"
    assert developer_run.status_code == 201


def test_workspace_permission_matrix_is_workspace_scoped(
    client: TestClient, db_session: Session
) -> None:
    register(client, "matrix-owner@example.com")
    owner_token = login(client, "matrix-owner@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Permission Matrix Workspace"},
        headers=auth_headers(owner_token),
    ).json()
    register(client, "matrix-viewer@example.com")
    viewer_token = login(client, "matrix-viewer@example.com")
    add_workspace_member(
        db_session,
        workspace_id=workspace["id"],
        user_email="matrix-viewer@example.com",
        role=WorkspaceRole.viewer,
    )
    register(client, "matrix-other@example.com")
    other_token = login(client, "matrix-other@example.com")

    viewer_matrix = client.get(
        f"/api/v1/workspaces/{workspace['id']}/permission-matrix",
        headers=auth_headers(viewer_token),
    )
    other_matrix = client.get(
        f"/api/v1/workspaces/{workspace['id']}/permission-matrix",
        headers=auth_headers(other_token),
    )

    assert viewer_matrix.status_code == 200
    roles = {entry["role"]: entry["permissions"] for entry in viewer_matrix.json()["roles"]}
    assert "owner" in roles
    assert "workspace:manage" in roles["owner"]
    assert "viewer" in roles
    assert "data:write" not in roles["viewer"]
    assert other_matrix.status_code == 404


def test_owner_can_archive_restore_and_archived_workspace_is_read_only(
    client: TestClient, db_session: Session
) -> None:
    register(client, "archive-owner@example.com")
    owner_token = login(client, "archive-owner@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Archive Workspace"},
        headers=auth_headers(owner_token),
    ).json()
    developer = register(client, "archive-developer@example.com")
    developer_token = login(client, "archive-developer@example.com")
    register(client, "archive-reviewer@example.com")
    add_workspace_member(
        db_session,
        workspace_id=workspace["id"],
        user_email="archive-developer@example.com",
        role=WorkspaceRole.developer,
    )

    non_owner_archive = client.post(
        f"/api/v1/workspaces/{workspace['id']}/archive",
        headers=auth_headers(developer_token),
    )
    archived = client.post(
        f"/api/v1/workspaces/{workspace['id']}/archive",
        headers=auth_headers(owner_token),
    )
    read_datasets = client.get(
        f"/api/v1/workspaces/{workspace['id']}/datasets",
        headers=auth_headers(owner_token),
    )
    blocked_import = client.post(
        f"/api/v1/workspaces/{workspace['id']}/datasets/import",
        headers=auth_headers(owner_token),
        json={
            "dataset_name": "Blocked Import",
            "source_type": "jsonl",
            "content": '{"messages":[{"role":"user","content":"Can I get a refund?"}]}',
        },
    )
    blocked_rename = client.patch(
        f"/api/v1/workspaces/{workspace['id']}",
        headers=auth_headers(owner_token),
        json={"name": "Archived Rename"},
    )
    blocked_member_add = client.post(
        f"/api/v1/workspaces/{workspace['id']}/members",
        headers=auth_headers(owner_token),
        json={"email": "archive-reviewer@example.com", "role": "reviewer"},
    )
    blocked_member_update = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/members/{developer['id']}",
        headers=auth_headers(owner_token),
        json={"role": "viewer"},
    )
    blocked_member_remove = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/members/{developer['id']}",
        headers=auth_headers(owner_token),
    )
    restored = client.post(
        f"/api/v1/workspaces/{workspace['id']}/restore",
        headers=auth_headers(owner_token),
    )
    allowed_import = client.post(
        f"/api/v1/workspaces/{workspace['id']}/datasets/import",
        headers=auth_headers(owner_token),
        json={
            "dataset_name": "Allowed Import",
            "source_type": "jsonl",
            "content": '{"messages":[{"role":"user","content":"Can I get a refund?"}]}',
        },
    )

    assert non_owner_archive.status_code == 403
    assert non_owner_archive.json()["detail"]["code"] == "workspace_owner_required"
    assert archived.status_code == 200
    assert archived.json()["archived_at"] is not None
    assert read_datasets.status_code == 200
    assert blocked_import.status_code == 409
    assert blocked_import.json()["detail"]["code"] == "workspace_archived"
    assert blocked_rename.status_code == 409
    assert blocked_rename.json()["detail"]["code"] == "workspace_archived"
    assert blocked_member_add.status_code == 409
    assert blocked_member_update.status_code == 409
    assert blocked_member_remove.status_code == 409
    assert restored.status_code == 200
    assert restored.json()["archived_at"] is None
    assert allowed_import.status_code == 201


def test_workspace_delete_requires_owner_and_exact_confirmation(client: TestClient) -> None:
    register(client, "delete-owner@example.com")
    owner_token = login(client, "delete-owner@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Delete Workspace"},
        headers=auth_headers(owner_token),
    ).json()
    register(client, "delete-other@example.com")
    other_token = login(client, "delete-other@example.com")

    non_member_delete = client.request(
        "DELETE",
        f"/api/v1/workspaces/{workspace['id']}",
        headers=auth_headers(other_token),
        json={"confirmation_name": "Delete Workspace"},
    )
    mismatch = client.request(
        "DELETE",
        f"/api/v1/workspaces/{workspace['id']}",
        headers=auth_headers(owner_token),
        json={"confirmation_name": "delete workspace"},
    )
    deleted = client.request(
        "DELETE",
        f"/api/v1/workspaces/{workspace['id']}",
        headers=auth_headers(owner_token),
        json={"confirmation_name": "Delete Workspace"},
    )
    after_delete_list = client.get("/api/v1/workspaces", headers=auth_headers(owner_token))
    after_delete_detail = client.get(
        f"/api/v1/workspaces/{workspace['id']}", headers=auth_headers(owner_token)
    )
    recreate = client.post(
        "/api/v1/workspaces",
        json={"name": "Delete Workspace"},
        headers=auth_headers(owner_token),
    )

    assert non_member_delete.status_code == 404
    assert mismatch.status_code == 409
    assert mismatch.json()["detail"]["code"] == "workspace_delete_confirmation_mismatch"
    assert deleted.status_code == 204
    assert after_delete_list.status_code == 200
    assert after_delete_list.json() == []
    assert after_delete_detail.status_code == 404
    assert recreate.status_code == 201


def test_workspace_leave_allows_members_and_preserves_last_owner(
    client: TestClient, db_session: Session
) -> None:
    owner = register(client, "leave-owner@example.com")
    owner_token = login(client, "leave-owner@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Leave Workspace"},
        headers=auth_headers(owner_token),
    ).json()
    register(client, "leave-developer@example.com")
    developer_token = login(client, "leave-developer@example.com")
    add_workspace_member(
        db_session,
        workspace_id=workspace["id"],
        user_email="leave-developer@example.com",
        role=WorkspaceRole.developer,
    )

    developer_leave = client.post(
        f"/api/v1/workspaces/{workspace['id']}/leave",
        headers=auth_headers(developer_token),
    )
    developer_detail = client.get(
        f"/api/v1/workspaces/{workspace['id']}",
        headers=auth_headers(developer_token),
    )
    last_owner_leave = client.post(
        f"/api/v1/workspaces/{workspace['id']}/leave",
        headers=auth_headers(owner_token),
    )

    assert owner["email"] == "leave-owner@example.com"
    assert developer_leave.status_code == 204
    assert developer_detail.status_code == 404
    assert last_owner_leave.status_code == 409
    assert last_owner_leave.json()["detail"]["code"] == "workspace_owner_guard"
