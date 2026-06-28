import json

from fastapi.testclient import TestClient

from app.core.language import LanguageDetectionError, SupportedLanguage, detect_language
from app.services.import_parser import ImportParseError, parse_csv, parse_jsonl


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


def test_language_detection_for_v1_languages() -> None:
    assert detect_language("Can I get a refund?") == SupportedLanguage.en
    assert detect_language("返金できますか？") == SupportedLanguage.ja
    assert detect_language("可以退款吗？") == SupportedLanguage.zh


def test_language_detection_rejects_empty_text() -> None:
    try:
        detect_language("   ")
    except LanguageDetectionError as exc:
        assert "empty" in str(exc)
    else:
        raise AssertionError("expected LanguageDetectionError")


def test_jsonl_parser_rejects_invalid_lines_without_dumping_content() -> None:
    try:
        parse_jsonl('{"messages": [')
    except ImportParseError as exc:
        assert str(exc) == "Invalid JSONL at line 1."
    else:
        raise AssertionError("expected ImportParseError")


def test_csv_parser_handles_required_columns_and_labels() -> None:
    examples = parse_csv(
        "external_id,role,content,label_intent,label_product_area\n"
        "en_001,user,Can I get a refund?,refund_request,billing\n"
    )

    assert len(examples) == 1
    assert examples[0].external_id == "en_001"
    assert examples[0].messages[0].content == "Can I get a refund?"
    assert examples[0].labels


def test_csv_parser_rejects_missing_required_columns() -> None:
    try:
        parse_csv("external_id,content\nen_001,Can I get a refund?\n")
    except ImportParseError as exc:
        assert "role and content" in str(exc)
    else:
        raise AssertionError("expected ImportParseError")


def test_import_jsonl_stores_multilingual_examples_messages_and_labels(client: TestClient) -> None:
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    workspace = create_workspace(client, token)

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/datasets/import",
        headers=auth_headers(token),
        json={
            "dataset_name": "Support Examples",
            "description": "Multilingual import",
            "source_type": "jsonl",
            "content": jsonl_content(
                {
                    "external_id": "en_refund_001",
                    "messages": [{"role": "user", "content": "Can I get a refund?"}],
                    "labels": {"intent": "refund_request", "product_area": "billing"},
                },
                {
                    "external_id": "ja_refund_001",
                    "messages": [{"role": "user", "content": "返金できますか？"}],
                    "labels": {"intent": "refund_request"},
                },
                {
                    "external_id": "zh_privacy_001",
                    "messages": [{"role": "user", "content": "你们泄露了我的个人信息。"}],
                    "labels": {"safety_risk": "high"},
                },
            ),
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["imported_examples"] == 3
    assert body["import_batch"]["status"] == "completed"

    dataset_id = body["dataset"]["id"]
    examples_response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/datasets/{dataset_id}/examples",
        headers=auth_headers(token),
    )
    assert examples_response.status_code == 200
    examples = examples_response.json()
    assert [example["language"] for example in examples] == ["en", "ja", "zh"]
    assert examples[0]["messages"][0]["language"] == "en"
    assert {label["label_type"] for label in examples[0]["labels"]} == {
        "intent",
        "product_area",
    }


def test_import_csv_and_list_datasets(client: TestClient) -> None:
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    workspace = create_workspace(client, token)

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/datasets/import",
        headers=auth_headers(token),
        json={
            "dataset_name": "CSV Examples",
            "source_type": "csv",
            "content": "external_id,role,content,label_intent\n"
            "en_001,user,Can I change my plan?,plan_change\n",
        },
    )

    assert response.status_code == 201
    list_response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/datasets", headers=auth_headers(token)
    )
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["total"] == 1
    assert body["limit"] is None
    assert body["offset"] == 0
    assert body["has_next"] is False
    assert [dataset["name"] for dataset in body["items"]] == ["CSV Examples"]


def test_manual_label_edit_creates_and_replaces_human_label(client: TestClient) -> None:
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    workspace = create_workspace(client, token)
    import_response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/datasets/import",
        headers=auth_headers(token),
        json={
            "dataset_name": "Support Examples",
            "source_type": "jsonl",
            "content": jsonl_content(
                {"messages": [{"role": "user", "content": "Can I get a refund?"}]}
            ),
        },
    )
    dataset_id = import_response.json()["dataset"]["id"]
    examples = client.get(
        f"/api/v1/workspaces/{workspace['id']}/datasets/{dataset_id}/examples",
        headers=auth_headers(token),
    ).json()
    example_id = examples[0]["id"]

    first = client.post(
        f"/api/v1/workspaces/{workspace['id']}/examples/{example_id}/labels",
        headers=auth_headers(token),
        json={"label_type": "intent", "value": "refund_request"},
    )
    second = client.post(
        f"/api/v1/workspaces/{workspace['id']}/examples/{example_id}/labels",
        headers=auth_headers(token),
        json={"label_type": "intent", "value": "billing_refund"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["value"] == "billing_refund"
    assert second.json()["source"] == "human"


def test_dataset_routes_enforce_workspace_isolation(client: TestClient) -> None:
    register(client, "owner@example.com")
    owner_token = login(client, "owner@example.com")
    owner_workspace = create_workspace(client, owner_token, "Owner Workspace")
    import_response = client.post(
        f"/api/v1/workspaces/{owner_workspace['id']}/datasets/import",
        headers=auth_headers(owner_token),
        json={
            "dataset_name": "Private Examples",
            "source_type": "jsonl",
            "content": jsonl_content(
                {"messages": [{"role": "user", "content": "Can I get a refund?"}]}
            ),
        },
    )
    dataset_id = import_response.json()["dataset"]["id"]
    owner_examples = client.get(
        f"/api/v1/workspaces/{owner_workspace['id']}/datasets/{dataset_id}/examples",
        headers=auth_headers(owner_token),
    ).json()
    example_id = owner_examples[0]["id"]

    register(client, "other@example.com")
    other_token = login(client, "other@example.com")
    other_workspace = create_workspace(client, other_token, "Other Workspace")

    forbidden_dataset = client.get(
        f"/api/v1/workspaces/{other_workspace['id']}/datasets/{dataset_id}/examples",
        headers=auth_headers(other_token),
    )
    forbidden_label = client.post(
        f"/api/v1/workspaces/{other_workspace['id']}/examples/{example_id}/labels",
        headers=auth_headers(other_token),
        json={"label_type": "intent", "value": "refund_request"},
    )

    assert forbidden_dataset.status_code == 404
    assert forbidden_dataset.json()["detail"]["code"] == "dataset_not_found"
    assert forbidden_label.status_code == 404
    assert forbidden_label.json()["detail"]["code"] == "example_not_found"


def test_dataset_routes_reject_unauthenticated_requests(client: TestClient) -> None:
    response = client.get("/api/v1/workspaces/00000000-0000-0000-0000-000000000000/datasets")

    assert response.status_code == 401



def test_dataset_list_supports_folder_unfiled_search_and_offset(client: TestClient) -> None:
    register(client, "dataset-page-owner@example.com")
    token = login(client, "dataset-page-owner@example.com")
    workspace = create_workspace(client, token)
    folder_response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/resource-folders",
        headers=auth_headers(token),
        json={"resource_type": "dataset", "name": "Training data"},
    )
    assert folder_response.status_code == 201
    folder_id = folder_response.json()["id"]

    created_names: list[str] = []
    for index in range(4):
        name = f"Paged Dataset {index}"
        response = client.post(
            f"/api/v1/workspaces/{workspace['id']}/datasets/import",
            headers=auth_headers(token),
            json={
                "dataset_name": name,
                "description": f"Dataset page test {index}",
                "source_type": "jsonl",
                "folder_id": folder_id if index < 3 else None,
                "content": jsonl_content(
                    {"messages": [{"role": "user", "content": f"Message {index}"}]}
                ),
            },
        )
        assert response.status_code == 201
        created_names.append(name)

    first_page = client.get(
        f"/api/v1/workspaces/{workspace['id']}/datasets",
        headers=auth_headers(token),
        params={"folder_id": folder_id, "limit": 2, "offset": 0},
    )
    second_page = client.get(
        f"/api/v1/workspaces/{workspace['id']}/datasets",
        headers=auth_headers(token),
        params={"folder_id": folder_id, "limit": 2, "offset": 2},
    )
    unfiled_page = client.get(
        f"/api/v1/workspaces/{workspace['id']}/datasets",
        headers=auth_headers(token),
        params={"unfiled": True, "limit": 10},
    )
    search_page = client.get(
        f"/api/v1/workspaces/{workspace['id']}/datasets",
        headers=auth_headers(token),
        params={"folder_id": folder_id, "search": "Paged Dataset 1", "limit": 10},
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
    assert [item["name"] for item in first_body["items"]] == ["Paged Dataset 2", "Paged Dataset 1"]
    assert [item["name"] for item in second_body["items"]] == ["Paged Dataset 0"]
    assert [item["name"] for item in unfiled_body["items"]] == ["Paged Dataset 3"]
    assert [item["name"] for item in search_body["items"]] == ["Paged Dataset 1"]
    assert created_names == [
        "Paged Dataset 0",
        "Paged Dataset 1",
        "Paged Dataset 2",
        "Paged Dataset 3",
    ]


def test_dataset_list_rejects_folder_and_unfiled_conflict(client: TestClient) -> None:
    register(client, "dataset-conflict-owner@example.com")
    token = login(client, "dataset-conflict-owner@example.com")
    workspace = create_workspace(client, token)
    folder_response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/resource-folders",
        headers=auth_headers(token),
        json={"resource_type": "dataset", "name": "Training data"},
    )
    assert folder_response.status_code == 201

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/datasets",
        headers=auth_headers(token),
        params={"folder_id": folder_response.json()["id"], "unfiled": True},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "dataset_filter_conflict"
