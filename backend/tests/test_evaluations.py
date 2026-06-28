import json

from fastapi.testclient import TestClient

from app.core.language import SupportedLanguage
from app.models.evaluation import EvaluationResult
from app.services.evaluation_loader import EvaluationCaseLoadError, load_jsonl_cases
from app.services.evaluation_metrics import calculate_metrics


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


def upload_refund_documents(client: TestClient, token: str, workspace_id: str) -> None:
    docs = [
        ("Refund Policy EN", "en", "Refunds are available within 30 days after purchase. " * 40),
        ("Refund Policy JA", "ja", "返金は購入から30日以内に申請できます。" * 40),
        ("Refund Policy ZH", "zh", "购买后30天内可以申请退款。" * 40),
    ]
    for title, language, content in docs:
        response = client.post(
            f"/api/v1/workspaces/{workspace_id}/knowledge-documents",
            headers=auth_headers(token),
            json={
                "title": title,
                "content_type": "text/plain",
                "language": language,
                "content": content,
            },
        )
        assert response.status_code == 201


def create_folder(
    client: TestClient, token: str, workspace_id: str, resource_type: str, name: str
) -> dict:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/resource-folders",
        headers=auth_headers(token),
        json={"resource_type": resource_type, "name": name},
    )
    assert response.status_code == 201
    return response.json()


def jsonl_content(*rows: dict) -> str:
    return "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)


def run_simple_evaluation(
    client: TestClient,
    token: str,
    workspace_id: str,
    name: str = "Lifecycle Evaluation",
) -> dict:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/evaluations",
        headers=auth_headers(token),
        json={
            "name": name,
            "modes": ["direct_llm"],
            "jsonl_cases": jsonl_content(
                {
                    "id": "en_refund_lifecycle_001",
                    "language": "en",
                    "input_message": "Can I get a refund within 30 days?",
                    "expected_route": "finalize",
                }
            ),
        },
    )
    assert response.status_code == 201
    return response.json()["run"]


def test_jsonl_loader_validates_cases() -> None:
    cases = load_jsonl_cases(
        jsonl_content(
            {
                "id": "ja_refund_001",
                "language": "ja",
                "input_message": "返金は30日以内にできますか？",
                "expected_route": "finalize",
                "must_include": ["30日以内"],
            }
        )
    )

    assert len(cases) == 1
    assert cases[0].external_id == "ja_refund_001"
    assert cases[0].language == SupportedLanguage.ja

    try:
        load_jsonl_cases('{"id":')
    except EvaluationCaseLoadError as exc:
        assert "Invalid JSONL" in str(exc)
    else:
        raise AssertionError("expected EvaluationCaseLoadError")


def test_metric_calculation_groups_by_mode_and_language() -> None:
    result = EvaluationResult(
        workspace_id="00000000-0000-0000-0000-000000000000",
        evaluation_run_id="00000000-0000-0000-0000-000000000000",
        evaluation_case_id="00000000-0000-0000-0000-000000000000",
        mode="system_v1",
        language="en",
        actual_route="finalize",
        answer="Refunds are available within 30 days.",
        citations_json="[]",
        passed=True,
        scores_json=json.dumps(
            {
                "route_match": 1.0,
                "language_preserved": 1.0,
                "citation_accuracy": 1.0,
                "groundedness": 1.0,
            }
        ),
        latency_ms=10,
        prompt_tokens=20,
        estimated_cost=0.01,
    )

    metrics = calculate_metrics([result])

    assert metrics[("system_v1", "en")]["case_pass_rate"] == 1.0
    assert metrics[("system_v1", "en")]["average_prompt_tokens"] == 20.0


def test_evaluation_api_runs_baselines_and_system_v1(client: TestClient) -> None:
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    workspace = create_workspace(client, token)
    upload_refund_documents(client, token, workspace["id"])

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/evaluations",
        headers=auth_headers(token),
        json={
            "name": "Smoke Evaluation",
            "modes": ["direct_llm", "vector_rag", "system_v1"],
            "jsonl_cases": jsonl_content(
                {
                    "id": "en_refund_001",
                    "language": "en",
                    "input_message": "Can I get a refund within 30 days?",
                    "expected_route": "finalize",
                    "must_include": ["30 days"],
                    "must_not_include": ["unconditional"],
                },
                {
                    "id": "ja_no_source_001",
                    "language": "ja",
                    "input_message": "アカウントを完全に削除する方法を教えてください。",
                    "expected_route": "human_review",
                    "must_not_include": ["できます"],
                },
                {
                    "id": "zh_refund_001",
                    "language": "zh",
                    "input_message": "我可以在30天内申请退款吗？",
                    "expected_route": "finalize",
                    "must_include": ["30天"],
                },
            ),
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["run"]["status"] == "completed"
    assert body["run"]["total_cases"] == 3
    assert len(body["results"]) == 9
    modes = {result["mode"] for result in body["results"]}
    languages = {result["language"] for result in body["results"]}
    assert modes == {"direct_llm", "vector_rag", "system_v1"}
    assert languages == {"en", "ja", "zh"}
    metric_keys = {(metric["mode"], metric["language"]) for metric in body["metrics"]}
    assert ("system_v1", "en") in metric_keys
    assert ("vector_rag", "zh") in metric_keys

    detail = client.get(
        f"/api/v1/workspaces/{workspace['id']}/evaluations/{body['run']['id']}",
        headers=auth_headers(token),
    )
    listed = client.get(
        f"/api/v1/workspaces/{workspace['id']}/evaluations",
        headers=auth_headers(token),
    )
    assert detail.status_code == 200
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == body["run"]["id"]


def test_evaluation_routes_enforce_workspace_isolation(client: TestClient) -> None:
    register(client, "owner@example.com")
    owner_token = login(client, "owner@example.com")
    owner_workspace = create_workspace(client, owner_token, "Owner Workspace")
    upload_refund_documents(client, owner_token, owner_workspace["id"])
    run = client.post(
        f"/api/v1/workspaces/{owner_workspace['id']}/evaluations",
        headers=auth_headers(owner_token),
        json={
            "name": "Private Evaluation",
            "modes": ["vector_rag"],
            "jsonl_cases": jsonl_content(
                {
                    "id": "en_refund_001",
                    "language": "en",
                    "input_message": "Can I get a refund within 30 days?",
                    "expected_route": "finalize",
                }
            ),
        },
    ).json()

    register(client, "other@example.com")
    other_token = login(client, "other@example.com")
    other_workspace = create_workspace(client, other_token, "Other Workspace")

    forbidden = client.get(
        f"/api/v1/workspaces/{other_workspace['id']}/evaluations/{run['run']['id']}",
        headers=auth_headers(other_token),
    )

    assert forbidden.status_code == 404
    assert forbidden.json()["detail"]["code"] == "evaluation_not_found"


def test_owner_can_archive_evaluation_run_without_losing_detail(client: TestClient) -> None:
    register(client, "eval-archive-owner@example.com")
    token = login(client, "eval-archive-owner@example.com")
    workspace = create_workspace(client, token)
    run = run_simple_evaluation(client, token, workspace["id"])

    archive = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/evaluations/{run['id']}",
        headers=auth_headers(token),
    )
    listed_default = client.get(
        f"/api/v1/workspaces/{workspace['id']}/evaluations",
        headers=auth_headers(token),
    )
    listed_with_archive = client.get(
        f"/api/v1/workspaces/{workspace['id']}/evaluations",
        headers=auth_headers(token),
        params={"include_archived": True},
    )
    detail = client.get(
        f"/api/v1/workspaces/{workspace['id']}/evaluations/{run['id']}",
        headers=auth_headers(token),
    )

    assert archive.status_code == 204
    assert listed_default.status_code == 200
    assert [item["id"] for item in listed_default.json()] == []
    assert listed_with_archive.status_code == 200
    archived_run = listed_with_archive.json()[0]
    assert archived_run["id"] == run["id"]
    assert archived_run["archived_at"] is not None
    assert detail.status_code == 200
    assert detail.json()["run"]["archived_at"] is not None
    assert len(detail.json()["results"]) == 1


def test_evaluation_archive_requires_owner_and_workspace_scope(client: TestClient) -> None:
    register(client, "eval-owner@example.com")
    owner_token = login(client, "eval-owner@example.com")
    owner_workspace = create_workspace(client, owner_token, "Owner Eval Workspace")
    run = run_simple_evaluation(client, owner_token, owner_workspace["id"])

    register(client, "eval-member@example.com")
    member_token = login(client, "eval-member@example.com")
    add_member = client.post(
        f"/api/v1/workspaces/{owner_workspace['id']}/members",
        headers=auth_headers(owner_token),
        json={"email": "eval-member@example.com", "role": "member"},
    )
    assert add_member.status_code == 201

    member_archive = client.delete(
        f"/api/v1/workspaces/{owner_workspace['id']}/evaluations/{run['id']}",
        headers=auth_headers(member_token),
    )

    register(client, "eval-other-owner@example.com")
    other_token = login(client, "eval-other-owner@example.com")
    other_workspace = create_workspace(client, other_token, "Other Eval Workspace")
    cross_workspace_archive = client.delete(
        f"/api/v1/workspaces/{other_workspace['id']}/evaluations/{run['id']}",
        headers=auth_headers(other_token),
    )

    assert member_archive.status_code == 403
    assert member_archive.json()["detail"]["code"] == "workspace_permission_required"
    assert member_archive.json()["detail"]["required_permission"] == "resources:delete"
    assert cross_workspace_archive.status_code == 404
    assert cross_workspace_archive.json()["detail"]["code"] == "evaluation_not_found"


def test_evaluation_runs_can_be_foldered_filtered_and_moved(client: TestClient) -> None:
    register(client, "eval-folder-owner@example.com")
    token = login(client, "eval-folder-owner@example.com")
    workspace = create_workspace(client, token)
    folder = create_folder(client, token, workspace["id"], "evaluation_run", "Regression packs")
    other_folder = create_folder(client, token, workspace["id"], "evaluation_run", "Release checks")

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/evaluations",
        headers=auth_headers(token),
        json={
            "name": "Foldered Evaluation",
            "folder_id": folder["id"],
            "modes": ["direct_llm"],
            "jsonl_cases": jsonl_content(
                {
                    "id": "en_foldered_eval_001",
                    "language": "en",
                    "input_message": "Can I get a refund within 30 days?",
                    "expected_route": "finalize",
                }
            ),
        },
    )

    assert response.status_code == 201
    run = response.json()["run"]
    assert run["folder_id"] == folder["id"]

    filtered = client.get(
        f"/api/v1/workspaces/{workspace['id']}/evaluations",
        headers=auth_headers(token),
        params={"folder_id": folder["id"]},
    )
    empty_other_folder = client.get(
        f"/api/v1/workspaces/{workspace['id']}/evaluations",
        headers=auth_headers(token),
        params={"folder_id": other_folder["id"]},
    )
    moved = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/evaluations/{run['id']}/folder",
        headers=auth_headers(token),
        json={"folder_id": other_folder["id"]},
    )
    filtered_after_move = client.get(
        f"/api/v1/workspaces/{workspace['id']}/evaluations",
        headers=auth_headers(token),
        params={"folder_id": other_folder["id"]},
    )

    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()] == [run["id"]]
    assert empty_other_folder.status_code == 200
    assert empty_other_folder.json() == []
    assert moved.status_code == 200
    assert moved.json()["folder_id"] == other_folder["id"]
    assert [item["id"] for item in filtered_after_move.json()] == [run["id"]]


def test_evaluation_folders_reject_wrong_type_and_foreign_workspace(client: TestClient) -> None:
    register(client, "eval-folder-a@example.com")
    token_a = login(client, "eval-folder-a@example.com")
    workspace_a = create_workspace(client, token_a, "Workspace A")
    dataset_folder = create_folder(client, token_a, workspace_a["id"], "dataset", "Datasets")
    eval_folder = create_folder(client, token_a, workspace_a["id"], "evaluation_run", "Eval A")
    run = run_simple_evaluation(client, token_a, workspace_a["id"])

    wrong_type = client.patch(
        f"/api/v1/workspaces/{workspace_a['id']}/evaluations/{run['id']}/folder",
        headers=auth_headers(token_a),
        json={"folder_id": dataset_folder["id"]},
    )

    register(client, "eval-folder-b@example.com")
    token_b = login(client, "eval-folder-b@example.com")
    workspace_b = create_workspace(client, token_b, "Workspace B")
    foreign_folder_create = client.post(
        f"/api/v1/workspaces/{workspace_b['id']}/evaluations",
        headers=auth_headers(token_b),
        json={
            "name": "Foreign folder attempt",
            "folder_id": eval_folder["id"],
            "modes": ["direct_llm"],
            "jsonl_cases": jsonl_content(
                {
                    "id": "en_foreign_folder_eval_001",
                    "language": "en",
                    "input_message": "Can I get a refund?",
                    "expected_route": "finalize",
                }
            ),
        },
    )
    foreign_folder_list = client.get(
        f"/api/v1/workspaces/{workspace_b['id']}/evaluations",
        headers=auth_headers(token_b),
        params={"folder_id": eval_folder["id"]},
    )

    assert wrong_type.status_code == 404
    assert wrong_type.json()["detail"]["code"] == "resource_folder_not_found"
    assert foreign_folder_create.status_code == 404
    assert foreign_folder_create.json()["detail"]["code"] == "resource_folder_not_found"
    assert foreign_folder_list.status_code == 404
    assert foreign_folder_list.json()["detail"]["code"] == "resource_folder_not_found"
