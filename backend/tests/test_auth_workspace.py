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


def test_workspace_membership_endpoint_returns_member_permissions(
    client: TestClient, db_session: Session
) -> None:
    register(client, "owner-member-permissions@example.com")
    owner_token = login(client, "owner-member-permissions@example.com")
    workspace = client.post(
        "/api/v1/workspaces",
        json={"name": "Member Permission Workspace"},
        headers=auth_headers(owner_token),
    ).json()

    register(client, "plain-member@example.com")
    member_token = login(client, "plain-member@example.com")
    add_workspace_member(
        db_session,
        workspace_id=workspace["id"],
        user_email="plain-member@example.com",
        role=WorkspaceRole.member,
    )

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/membership",
        headers=auth_headers(member_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "member"
    assert body["can_manage_resources"] is False
    assert body["can_manage_workspace"] is False
    assert "workspace:read" in body["permissions"]
    assert "tasks:read" in body["permissions"]
    assert "knowledge:read" in body["permissions"]
    assert "tools:read" in body["permissions"]
    assert "reviews:read" in body["permissions"]
    assert "prompts:read" in body["permissions"]
    assert "models:read" in body["permissions"]
    assert "settings:read" in body["permissions"]
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
