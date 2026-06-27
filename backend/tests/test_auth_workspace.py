from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token, hash_password, verify_password
from app.models.user import User


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
