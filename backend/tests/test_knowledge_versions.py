from test_knowledge_documents import auth_headers, create_workspace, login, register


def test_version_reads_preserve_history_and_enforce_workspace_access(client):
    register(client, "version-owner@example.test")
    token = login(client, "version-owner@example.test")
    headers = auth_headers(token)
    workspace = create_workspace(client, token)
    base = f"/api/v1/workspaces/{workspace['id']}/knowledge-documents"
    created = client.post(
        base,
        headers=headers,
        json={
            "title": "Policy",
            "content": "Original policy 日本語 中文",
            "content_type": "text/plain",
        },
    )
    assert created.status_code == 201
    document = created.json()["document"]["id"]
    path = f"{base}/{document}/versions/1"
    changed = client.post(
        f"{base}/{document}/reindex",
        headers=headers,
        json={
            "title": "Changed policy",
            "content": "Replacement policy",
            "language": "en",
        },
    )
    assert changed.status_code == 200
    original = client.get(path, headers=headers)
    assert original.status_code == 200
    assert original.json()["raw_text"] == "Original policy 日本語 中文"
    assert original.json()["version"] == 1
    assert (
        client.get(f"{base}/{document}/versions/2", headers=headers).json()["raw_text"]
        == "Replacement policy"
    )
    assert client.get(path).status_code == 401
    assert client.get(f"{base}/{document}/versions/99", headers=headers).status_code == 404
    assert client.get(f"{base}/{document}/versions/0", headers=headers).status_code == 422
    other = create_workspace(client, token, "Other")
    assert (
        client.get(path.replace(workspace["id"], other["id"]), headers=headers).status_code == 404
    )
    register(client, "version-viewer@example.test")
    viewer_headers = auth_headers(login(client, "version-viewer@example.test"))
    assert client.get(path, headers=viewer_headers).status_code == 404
    member = client.post(
        f"/api/v1/workspaces/{workspace['id']}/members",
        headers=headers,
        json={"email": "version-viewer@example.test", "role": "viewer"},
    )
    assert member.status_code == 201
    assert (
        client.get(path, headers=viewer_headers).json()["raw_text"] == original.json()["raw_text"]
    )
    assert client.delete(f"{base}/{document}", headers=headers).status_code == 204
    assert client.get(path, headers=headers).status_code == 404
