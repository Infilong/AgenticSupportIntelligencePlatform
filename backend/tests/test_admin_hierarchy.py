from uuid import UUID

from app.models.workspace import WorkspaceRole
from app.services.workspace_service import permissions_for_role


def account(client, name):
    credentials = {"email": f"{name}@hierarchy.test", "password": "strong-password"}
    response = client.post("/api/v1/auth/register", json={**credentials, "display_name": name})
    assert response.status_code == 201
    token = client.post("/api/v1/auth/login", json=credentials).json()["access_token"]
    return response.json()["id"], credentials["email"], {"Authorization": f"Bearer {token}"}


def test_hierarchy_is_monotonic_without_promoting_legacy_roles():
    roles = [WorkspaceRole.viewer, WorkspaceRole.operator, WorkspaceRole.admin, WorkspaceRole.owner]
    for lower, upper in zip(roles, roles[1:], strict=False):
        assert set(permissions_for_role(lower)) < set(permissions_for_role(upper))
    assert "members:manage" not in permissions_for_role(WorkspaceRole.developer)
    assert "models:write" not in permissions_for_role(WorkspaceRole.admin)
    assert "agents:configure" not in permissions_for_role(WorkspaceRole.operator)


def test_admin_can_manage_only_lower_roles_and_owner_can_assign_privileged_roles(client):
    owner, _, owner_headers = account(client, "owner")
    admin, admin_email, admin_headers = account(client, "admin")
    operator, operator_email, operator_headers = account(client, "operator")
    _, viewer_email, _ = account(client, "viewer")
    workspace = client.post("/api/v1/workspaces", headers=owner_headers,
                            json={"name": "Hierarchy"}).json()["id"]
    base = f"/api/v1/workspaces/{workspace}"
    assert client.post(base + "/members", headers=owner_headers,
                       json={"email": admin_email, "role": "admin"}).status_code == 201
    assert client.post(base + "/members", headers=admin_headers,
                       json={"email": operator_email, "role": "operator"}).status_code == 201
    assert client.post(base + "/members", headers=operator_headers,
                       json={"email": viewer_email, "role": "viewer"}).status_code == 403
    for role in ["admin", "owner", "developer", "member", "reviewer"]:
        expected = 409 if role in {"admin", "owner"} else 422
        assert client.post(base + "/members", headers=admin_headers,
                           json={"email": viewer_email, "role": role}).status_code == expected
        assert client.patch(base + f"/members/{operator}", headers=admin_headers,
                            json={"role": role}).status_code == expected
    for role in ["developer", "member", "reviewer"]:
        assert client.post(base + "/members", headers=owner_headers,
                           json={"email": viewer_email, "role": role}).status_code == 422
        assert client.patch(base + f"/members/{operator}", headers=owner_headers,
                            json={"role": role}).status_code == 422
    for target in [owner, admin]:
        assert client.patch(base + f"/members/{target}", headers=admin_headers,
                            json={"role": "viewer"}).status_code == 409
        assert client.delete(base + f"/members/{target}", headers=admin_headers).status_code == 409
    assert client.patch(base + f"/members/{operator}", headers=admin_headers,
                        json={"role": "viewer"}).status_code == 200
    assert client.delete(base + f"/members/{operator}", headers=admin_headers).status_code == 204
    assert client.post(base + "/members", headers=owner_headers,
                       json={"email": viewer_email}).json()["role"] == "viewer"
    assert client.post(base + "/leave", headers=owner_headers).status_code == 409
    filtered = client.get(base + "/members?limit=1&search=admin", headers=admin_headers)
    assert filtered.status_code == 200
    assert [member["user_id"] for member in filtered.json()] == [admin]
    assert client.get(base + "/members?limit=1&offset=1&search=admin",
                      headers=admin_headers).json() == []
    # A workspace outsider cannot use an Admin membership from another workspace.
    foreign = client.post("/api/v1/workspaces", headers=owner_headers,
                          json={"name": "Foreign"}).json()["id"]
    assert UUID(foreign) != UUID(workspace)
    assert client.get(f"/api/v1/workspaces/{foreign}/members",
                      headers=admin_headers).status_code == 404
