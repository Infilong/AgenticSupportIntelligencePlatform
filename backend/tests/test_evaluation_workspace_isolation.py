"""Valid IDs must remain scoped even when the caller owns both workspaces."""

import pytest

from app.services.model_provider import MockModelProvider
from tests.test_agents import create_workspace
from tests.test_evaluation_authorization_boundary import snapshot
from tests.test_resource_folders import create_folder
from tests.test_workflow_authorization import protected_workflow as protected_workflow


@pytest.mark.parametrize("direction", [0, 1])
def test_evaluation_ids_and_folders_cannot_cross_workspaces(
    client, db_session, monkeypatch, protected_workflow, direction,
):
    data = protected_workflow
    headers = data["owner"]
    token = headers["Authorization"].removeprefix("Bearer ")
    second = create_workspace(client, token, "Other evaluation workspace")
    bases = [data["base"], f"/api/v1/workspaces/{second['id']}"]
    created = client.post(bases[1] + "/evaluations", headers=headers,
                          json=data["evaluation_payload"])
    assert created.status_code == 201
    runs = [data["evaluation"], created.json()["run"]["id"]]
    folders = []
    for base, run in zip(bases, runs, strict=True):
        folders.append(create_folder(client, token, base.split("/")[-1],
                                     "evaluation_run", "Private folder")["id"])
        assert client.delete(f"{base}/evaluations/{run}", headers=headers).status_code == 204
        detail = client.get(f"{base}/evaluations/{run}", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["results"] and detail.json()["metrics"]
        listed = client.get(base + "/evaluations?include_archived=true", headers=headers)
        assert listed.status_code == 200
        assert [item["id"] for item in listed.json()] == [run]

    local, foreign = direction, 1 - direction
    base = bases[local] + "/evaluations"
    current, other = runs[local], runs[foreign]
    folder = folders[foreign]
    requests = [
        ("GET", f"{base}/{other}", None),
        ("GET", f"{base}/{current}/compare/{other}", None),
        ("GET", f"{base}/{other}/compare/{current}", None),
        ("PATCH", f"{base}/{other}/folder", {"folder_id": folders[local]}),
        ("PATCH", f"{base}/{current}/folder", {"folder_id": folder}),
        ("DELETE", f"{base}/{other}", None),
        ("DELETE", f"{base}/{other}/permanent", None),
        ("GET", f"{base}?include_archived=true&folder_id={folder}", None),
        ("POST", base, {**data["evaluation_payload"], "folder_id": folder}),
    ]

    def forbidden(*args, **kwargs):
        pytest.fail("Cross-workspace operation dispatched a model call")

    monkeypatch.setattr(MockModelProvider, "complete", forbidden)
    before = snapshot(db_session)
    for method, path, body in requests:
        response = client.request(method, path, headers=headers, json=body)
        assert response.status_code == 404, (method, path, response.text)
        assert "SENTINEL" not in response.text
        assert other not in response.text and folder not in response.text
        assert snapshot(db_session) == before
