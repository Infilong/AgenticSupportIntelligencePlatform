from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_retrieval import auth_headers, create_workspace, login, register, upload_document

from app.models.knowledge import DocumentVersion


@pytest.mark.parametrize("language,old,current", [
    ("en", "Refunds are allowed within 30 days.", "Refunds are allowed within 7 days."),
    ("ja", "返金は購入から30日以内に申請できます。", "返金は購入から7日以内に申請できます。"),
    ("zh", "购买后30天内可以申请退款。", "购买后7天内可以申请退款。"),
])
def test_retrieval_uses_only_latest_document_version(
    client: TestClient, db_session: Session, language, old, current,
):
    register(client, "versions@example.com")
    token = login(client, "versions@example.com")
    workspace = create_workspace(client, token)
    upload = upload_document(client, token, workspace["id"], title="Refund policy",
                             language=language, content=old * 20)
    document_id = upload["document"]["id"]
    base = f"/api/v1/workspaces/{workspace['id']}"
    updated = client.post(f"{base}/knowledge-documents/{document_id}/reindex",
                          headers=auth_headers(token),
                          json={"content": current * 20, "language": language,
                                "content_type": "text/plain"})
    assert updated.status_code == 200
    assert updated.json()["latest_version"]["version"] == 2
    response = client.post(f"{base}/retrieval/search", headers=auth_headers(token),
                           json={"query": old, "language": language, "min_score": 0,
                                 "top_k": 10, "document_id": document_id})
    assert response.status_code == 200
    results = response.json()["results"]
    assert results
    assert {item["version"] for item in results} == {2}
    assert all("30" not in item["content"] for item in results)
    versions = db_session.scalars(select(DocumentVersion.version).where(
        DocumentVersion.knowledge_document_id == UUID(document_id),
    )).all()
    assert set(versions) == {1, 2}
