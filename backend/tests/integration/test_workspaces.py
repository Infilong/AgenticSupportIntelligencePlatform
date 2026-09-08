from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.workspaces.models import Membership
from app.modules.workspaces.service import change_member
from tests.integration.conftest import login


def test_workspace_isolation_roles_and_csrf(system):
    client, workspace, foreign = system["client"], system["workspace"], system["foreign"]
    for role in ("viewer", "operator", "admin"):
        headers = login(client, role)
        assert [item["id"] for item in client.get("/api/workspaces").json()] == [str(workspace)]
        assert client.get(f"/api/workspaces/{foreign}").status_code == 404
        assert client.get(f"/api/workspaces/{workspace}").json()["role"] == role
        result = client.get(f"/api/workspaces/{workspace}/members")
        assert result.status_code == (200 if role == "admin" else 403)
        url = f"/api/workspaces/{workspace}/members/{system['users']['viewer'].id}"
        assert client.patch(url, json={"role": "operator"}).status_code == 403
        result = client.patch(url, json={"role": "viewer"}, headers=headers)
        assert result.status_code == (204 if role == "admin" else 403)
        assert (
            client.patch(
                f"/api/workspaces/{foreign}/members/{system['users']['other'].id}",
                json={"role": "viewer"},
                headers=headers,
            ).status_code
            == 404
        )


def test_last_admin_and_demotion_take_effect(system):
    client, workspace = system["client"], system["workspace"]
    headers = login(client)
    url = f"/api/workspaces/{workspace}/members/{system['users']['admin'].id}"
    assert client.patch(url, json={"role": "viewer"}, headers=headers).status_code == 409
    assert client.delete(url, headers=headers).status_code == 409
    other = system["users"]["operator"].id
    assert (
        client.patch(
            f"/api/workspaces/{workspace}/members/{other}", json={"role": "admin"}, headers=headers
        ).status_code
        == 204
    )
    assert client.patch(url, json={"role": "viewer"}, headers=headers).status_code == 204
    assert client.get(f"/api/workspaces/{workspace}/members").status_code == 403
    assert client.get(f"/api/workspaces/{workspace}").json()["role"] == "viewer"


@pytest.mark.parametrize("role", ["viewer", None])
def test_concurrent_changes_cannot_remove_all_admins(system, role):
    workspace = system["workspace"]
    first, second = system["users"]["admin"].id, system["users"]["operator"].id
    with Session(system["engine"]) as db:
        db.get(Membership, (workspace, second)).role = "admin"
        db.commit()
    barrier = Barrier(2)

    def demote(user):
        with Session(system["engine"]) as db:
            barrier.wait(timeout=10)
            try:
                change_member(db, workspace, user, user, role)
                return 204
            except HTTPException as error:
                return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(demote, (first, second)))
    assert sorted(outcomes) == [204, 409]
    with Session(system["engine"]) as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(Membership)
                .where(Membership.workspace_id == workspace, Membership.role == "admin")
            )
            == 1
        )


def test_removal_invalidates_existing_session_and_delete_denials(system):
    client, workspace = system["client"], system["workspace"]
    target = system["users"]["viewer"].id
    url = f"/api/workspaces/{workspace}/members/{target}"
    for role in ("viewer", "operator"):
        headers = login(client, role)
        assert client.delete(url, headers=headers).status_code == 403
    headers = login(client)
    assert (
        client.delete(f"/api/workspaces/{system['foreign']}/members/{target}", headers=headers).status_code
        == 404
    )
    # Removing one's membership with a second admin present invalidates this same session's workspace access.
    operator = system["users"]["operator"].id
    assert (
        client.patch(
            f"/api/workspaces/{workspace}/members/{operator}", json={"role": "admin"}, headers=headers
        ).status_code
        == 204
    )
    assert (
        client.delete(
            f"/api/workspaces/{workspace}/members/{system['users']['admin'].id}", headers=headers
        ).status_code
        == 204
    )
    assert client.get(f"/api/workspaces/{workspace}").status_code == 404
    assert client.get("/api/workspaces").json() == []
    assert client.delete(url, headers=headers).status_code == 404
