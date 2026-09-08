from itertools import pairwise
from uuid import UUID

from fastapi.testclient import TestClient
from pagination_fixtures import set_creation_order
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.knowledge import (
    DocumentChunk,
    DocumentStatus,
    DocumentVersion,
    Embedding,
    KnowledgeDocument,
)
from app.models.user import User
from app.services.chunking import chunk_text
from app.services.document_parser import DocumentParseError, parse_text_document
from app.services.embedding_provider import EmbeddingProvider, MockEmbeddingProvider
from app.services.knowledge_service import KnowledgeDocumentIndexError, KnowledgeService


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


def test_parser_accepts_text_and_rejects_unsupported_type() -> None:
    assert parse_text_document(content=" Policy text ", content_type="text/plain") == "Policy text"

    try:
        parse_text_document(content="%PDF", content_type="application/pdf")
    except DocumentParseError as exc:
        assert "Unsupported" in str(exc)
    else:
        raise AssertionError("expected DocumentParseError")


def test_language_aware_chunking_uses_word_and_cjk_windows() -> None:
    english = chunk_text(" ".join(f"word{i}" for i in range(240)), SupportedLanguage.en)
    japanese = chunk_text(
        "".join(f"返金ポリシー{i}です。" for i in range(220)),
        SupportedLanguage.ja,
    )
    chinese = chunk_text(
        "".join(f"退款政策适用于购买后{i}天内。" for i in range(220)),
        SupportedLanguage.zh,
    )

    assert len(english) > 1
    assert english[0].metadata["strategy"] == "word_window"
    assert len(japanese) > 1
    assert japanese[0].metadata["strategy"] == "cjk_sentence_window"
    assert len(chinese) > 1
    assert chinese[0].metadata["strategy"] == "cjk_sentence_window"


def test_chunking_collapses_adjacent_duplicate_cjk_sentences() -> None:
    chunks = chunk_text("退款政策适用于购买后三十天内。" * 80, SupportedLanguage.zh)

    combined = "".join(chunk.content for chunk in chunks)

    assert combined.count("退款政策适用于购买后三十天内。") == 1


def test_cjk_chunking_packs_sentences_without_duplicate_overlap() -> None:
    source = "退款政策适用于购买后三十天内。账单问题请在工作区设置中查看。" * 30

    chunks = chunk_text(source, SupportedLanguage.zh, max_tokens=24, overlap_tokens=6)

    assert len(chunks) > 1
    assert all(chunk.metadata["strategy"] == "cjk_sentence_window" for chunk in chunks)
    assert all(chunk.content.endswith(("。", "！", "？")) for chunk in chunks)
    for previous, current in pairwise(chunks):
        assert previous.content[-12:] != current.content[:12]


def test_cjk_chunking_uses_language_specific_token_counts() -> None:
    japanese = chunk_text(
        "購入から30日以内であれば返金できます。" * 12,
        SupportedLanguage.ja,
        max_tokens=18,
        overlap_tokens=4,
    )
    chinese = chunk_text(
        "购买后三十天内可以申请退款。" * 12,
        SupportedLanguage.zh,
        max_tokens=18,
        overlap_tokens=4,
    )

    assert japanese[0].token_count == chunk_text(
        japanese[0].content, SupportedLanguage.ja
    )[0].token_count
    assert chinese[0].token_count == chunk_text(
        chinese[0].content, SupportedLanguage.zh
    )[0].token_count


def test_mock_embedding_provider_is_deterministic_and_small() -> None:
    provider = MockEmbeddingProvider()

    first = provider.embed_texts(["返金できますか？"])[0]
    second = provider.embed_texts(["返金できますか？"])[0]

    assert first == second
    assert len(first) == 16
    assert all(-1 <= value <= 1 for value in first)


def test_upload_document_creates_version_chunks_and_embeddings(client: TestClient) -> None:
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    workspace = create_workspace(client, token)

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents",
        headers=auth_headers(token),
        json={
            "title": "Refund Policy JA",
            "content_type": "text/markdown",
            "language": "ja",
            "content": ("# 返金ポリシー\n購入から30日以内であれば返金を申請できます。" * 30),
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["document"]["status"] == "indexed"
    assert body["document"]["language"] == "ja"
    assert body["latest_version"]["version"] == 1
    assert body["chunk_count"] >= 1
    assert body["embedding_count"] == body["chunk_count"]

    detail = client.get(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents/{body['document']['id']}",
        headers=auth_headers(token),
    )
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["embedding_count"] == body["embedding_count"]
    assert detail_body["chunks"][0]["language"] == "ja"
    assert "30日以内" in "".join(chunk["content"] for chunk in detail_body["chunks"])


def test_upload_rejects_unsupported_file_type(client: TestClient) -> None:
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    workspace = create_workspace(client, token)

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents",
        headers=auth_headers(token),
        json={
            "title": "PDF Policy",
            "content_type": "application/pdf",
            "language": "en",
            "content": "%PDF raw bytes",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "knowledge_document_index_failed"


def test_list_detail_and_reindex_are_workspace_scoped(client: TestClient) -> None:
    register(client, "owner@example.com")
    owner_token = login(client, "owner@example.com")
    owner_workspace = create_workspace(client, owner_token, "Owner Workspace")
    upload = client.post(
        f"/api/v1/workspaces/{owner_workspace['id']}/knowledge-documents",
        headers=auth_headers(owner_token),
        json={
            "title": "Refund Policy",
            "content_type": "text/plain",
            "language": "en",
            "content": "Refunds are available within 30 days. " * 40,
        },
    )
    assert upload.status_code == 201
    document_id = upload.json()["document"]["id"]

    register(client, "other@example.com")
    other_token = login(client, "other@example.com")
    other_workspace = create_workspace(client, other_token, "Other Workspace")

    owner_list = client.get(
        f"/api/v1/workspaces/{owner_workspace['id']}/knowledge-documents",
        headers=auth_headers(owner_token),
    )
    forbidden_detail = client.get(
        f"/api/v1/workspaces/{other_workspace['id']}/knowledge-documents/{document_id}",
        headers=auth_headers(other_token),
    )
    forbidden_reindex = client.post(
        f"/api/v1/workspaces/{other_workspace['id']}/knowledge-documents/{document_id}/reindex",
        headers=auth_headers(other_token),
        json={"content": "Updated private policy", "content_type": "text/plain"},
    )

    assert owner_list.status_code == 200
    owner_body = owner_list.json()
    assert owner_body["total"] == 1
    assert owner_body["has_next"] is False
    assert [item["id"] for item in owner_body["items"]] == [document_id]
    assert forbidden_detail.status_code == 404
    assert forbidden_detail.json()["detail"]["code"] == "knowledge_document_not_found"
    assert forbidden_reindex.status_code == 404
    assert forbidden_reindex.json()["detail"]["code"] == "knowledge_document_not_found"


def test_reindex_creates_new_version(client: TestClient) -> None:
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    workspace = create_workspace(client, token)
    upload = client.post(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents",
        headers=auth_headers(token),
        json={
            "title": "Billing FAQ",
            "content_type": "text/plain",
            "language": "en",
            "content": "Billing plans can be changed from settings. " * 30,
        },
    )
    document_id = upload.json()["document"]["id"]

    reindex = client.post(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents/{document_id}/reindex",
        headers=auth_headers(token),
        json={
            "content_type": "text/plain",
            "title": "Updated Billing FAQ",
            "content": "Billing plans can be changed from workspace settings. " * 30,
        },
    )

    assert reindex.status_code == 200
    assert reindex.json()["document"]["title"] == "Updated Billing FAQ"
    assert reindex.json()["latest_version"]["version"] == 2

    detail = client.get(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents/{document_id}",
        headers=auth_headers(token),
    )
    assert detail.json()["document"]["title"] == "Updated Billing FAQ"
    assert detail.json()["latest_version"]["version"] == 2
    assert "workspace settings" in detail.json()["latest_version"]["raw_text"]


def test_delete_document_removes_workspace_document_and_index_rows(
    client: TestClient, db_session: Session
) -> None:
    register(client, "delete-owner@example.com")
    token = login(client, "delete-owner@example.com")
    workspace = create_workspace(client, token)
    upload = client.post(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents",
        headers=auth_headers(token),
        json={
            "title": "Obsolete Refund Policy",
            "content_type": "text/plain",
            "language": "en",
            "content": "Refunds are available within 30 days. " * 40,
        },
    )
    assert upload.status_code == 201
    document_id = upload.json()["document"]["id"]

    deleted = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents/{document_id}",
        headers=auth_headers(token),
    )
    detail = client.get(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents/{document_id}",
        headers=auth_headers(token),
    )
    listed = client.get(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents",
        headers=auth_headers(token),
    )

    assert deleted.status_code == 204
    assert detail.status_code == 404
    listed_body = listed.json()
    assert listed_body["items"] == []
    assert listed_body["total"] == 0
    assert listed_body["has_next"] is False
    assert db_session.scalar(select(KnowledgeDocument)) is None
    assert db_session.scalar(select(DocumentVersion)) is None
    assert db_session.scalar(select(DocumentChunk)) is None
    assert db_session.scalar(select(Embedding)) is None


def test_delete_document_is_workspace_scoped(client: TestClient) -> None:
    register(client, "delete-owner@example.com")
    owner_token = login(client, "delete-owner@example.com")
    owner_workspace = create_workspace(client, owner_token, "Owner Workspace")
    upload = client.post(
        f"/api/v1/workspaces/{owner_workspace['id']}/knowledge-documents",
        headers=auth_headers(owner_token),
        json={
            "title": "Private Refund Policy",
            "content_type": "text/plain",
            "language": "en",
            "content": "Refunds are available within 30 days. " * 40,
        },
    )
    assert upload.status_code == 201
    document_id = upload.json()["document"]["id"]

    register(client, "delete-other@example.com")
    other_token = login(client, "delete-other@example.com")
    other_workspace = create_workspace(client, other_token, "Other Workspace")

    forbidden = client.delete(
        f"/api/v1/workspaces/{other_workspace['id']}/knowledge-documents/{document_id}",
        headers=auth_headers(other_token),
    )
    owner_detail = client.get(
        f"/api/v1/workspaces/{owner_workspace['id']}/knowledge-documents/{document_id}",
        headers=auth_headers(owner_token),
    )

    assert forbidden.status_code == 404
    assert forbidden.json()["detail"]["code"] == "knowledge_document_not_found"
    assert owner_detail.status_code == 200


class FailingEmbeddingProvider(EmbeddingProvider):
    provider = "failing"
    model = "failing-test-provider"
    dimensions = 16

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("embedding backend unavailable")


class SpyEmbeddingProvider(EmbeddingProvider):
    provider = "spy"
    model = "spy-test-provider"
    dimensions = 16

    def __init__(self) -> None:
        self.received_texts: list[str] = []

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.received_texts = texts
        return [[0.1] * self.dimensions for _ in texts]


def test_indexing_failure_marks_document_failed(
    client: TestClient, db_session: Session
) -> None:
    user_body = register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    workspace = create_workspace(client, token)
    user = db_session.scalar(select(User).where(User.id == UUID(user_body["id"])))
    assert user is not None

    service = KnowledgeService(db_session, embedding_provider=FailingEmbeddingProvider())
    try:
        service.upload_document(
            workspace_id=UUID(workspace["id"]),
            title="Failing Policy",
            content_type="text/plain",
            content="Refund policy content. " * 40,
            language=SupportedLanguage.en,
            current_user=user,
        )
    except KnowledgeDocumentIndexError as exc:
        assert "embedding backend unavailable" in str(exc)
    else:
        raise AssertionError("expected KnowledgeDocumentIndexError")

    document = db_session.scalar(
        select(KnowledgeDocument).where(KnowledgeDocument.title == "Failing Policy")
    )
    assert document is not None
    assert document.status == DocumentStatus.failed
    assert "embedding backend unavailable" in (document.error_message or "")


def test_long_document_is_chunked_before_embedding(
    client: TestClient, db_session: Session
) -> None:
    user_body = register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    workspace = create_workspace(client, token)
    user = db_session.scalar(select(User).where(User.id == UUID(user_body["id"])))
    assert user is not None
    long_text = " ".join(f"policy-word-{index}" for index in range(900))
    provider = SpyEmbeddingProvider()

    result = KnowledgeService(db_session, embedding_provider=provider).upload_document(
        workspace_id=UUID(workspace["id"]),
        title="Long Policy",
        content_type="text/plain",
        content=long_text,
        language=SupportedLanguage.en,
        current_user=user,
    )

    assert result.chunk_count > 1
    assert len(provider.received_texts) == result.chunk_count
    assert long_text not in provider.received_texts
    assert all(len(text.split()) <= 180 for text in provider.received_texts)



def test_knowledge_document_list_supports_folder_unfiled_search_and_offset(
    client: TestClient, db_session,
) -> None:
    register(client, "knowledge-page-owner@example.com")
    token = login(client, "knowledge-page-owner@example.com")
    workspace = create_workspace(client, token)
    folder_response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/resource-folders",
        headers=auth_headers(token),
        json={"resource_type": "knowledge_document", "name": "Policies"},
    )
    assert folder_response.status_code == 201
    folder_id = folder_response.json()["id"]

    created_titles: list[str] = []
    for index in range(4):
        title = f"Paged Policy {index}"
        response = client.post(
            f"/api/v1/workspaces/{workspace['id']}/knowledge-documents",
            headers=auth_headers(token),
            json={
                "title": title,
                "content_type": "text/plain",
                "language": "en",
                "folder_id": folder_id if index < 3 else None,
                "content": f"{title} governs support behavior. " * 40,
            },
        )
        assert response.status_code == 201
        created_titles.append(title)

    set_creation_order(
        db_session, KnowledgeDocument, workspace["id"], created_titles, label="title"
    )

    first_page = client.get(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents",
        headers=auth_headers(token),
        params={"folder_id": folder_id, "limit": 2, "offset": 0},
    )
    second_page = client.get(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents",
        headers=auth_headers(token),
        params={"folder_id": folder_id, "limit": 2, "offset": 2},
    )
    unfiled_page = client.get(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents",
        headers=auth_headers(token),
        params={"unfiled": True, "limit": 10},
    )
    search_page = client.get(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents",
        headers=auth_headers(token),
        params={"folder_id": folder_id, "search": "Paged Policy 1", "limit": 10},
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert unfiled_page.status_code == 200
    assert search_page.status_code == 200
    first_body = first_page.json()
    second_body = second_page.json()
    unfiled_body = unfiled_page.json()
    search_body = search_page.json()
    assert first_body["total"] == 3
    assert first_body["limit"] == 2
    assert first_body["offset"] == 0
    assert first_body["has_next"] is True
    assert second_body["total"] == 3
    assert second_body["limit"] == 2
    assert second_body["offset"] == 2
    assert second_body["has_next"] is False
    assert unfiled_body["total"] == 1
    assert unfiled_body["has_next"] is False
    assert search_body["total"] == 1
    assert search_body["has_next"] is False
    assert [item["title"] for item in first_body["items"]] == ["Paged Policy 2", "Paged Policy 1"]
    assert [item["title"] for item in second_body["items"]] == ["Paged Policy 0"]
    assert [item["title"] for item in unfiled_body["items"]] == ["Paged Policy 3"]
    assert [item["title"] for item in search_body["items"]] == ["Paged Policy 1"]
    assert created_titles == [
        "Paged Policy 0",
        "Paged Policy 1",
        "Paged Policy 2",
        "Paged Policy 3",
    ]


def test_knowledge_document_list_rejects_folder_and_unfiled_conflict(client: TestClient) -> None:
    register(client, "knowledge-conflict-owner@example.com")
    token = login(client, "knowledge-conflict-owner@example.com")
    workspace = create_workspace(client, token)
    folder_response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/resource-folders",
        headers=auth_headers(token),
        json={"resource_type": "knowledge_document", "name": "Policies"},
    )
    assert folder_response.status_code == 201

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents",
        headers=auth_headers(token),
        params={"folder_id": folder_response.json()["id"], "unfiled": True},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "knowledge_document_filter_conflict"
