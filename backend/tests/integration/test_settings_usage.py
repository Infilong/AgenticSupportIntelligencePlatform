from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.usage.models import ModelCall
from tests.integration.conftest import login


def test_admin_defaults_persist_and_provider_configuration_has_no_secrets(system):
    client, ws = system["client"], system["workspace"]
    path = f"/api/workspaces/{ws}/settings"
    auth = login(client)
    current = client.get(path)
    assert current.status_code == 200 and current.json()["default_language"] == "en"
    config = current.json()
    assert config["generation_mode"] == "codex_assisted_development"
    assert not config["automatic_generation_available"] and config["retrieval_strategy"] == "vector_rerank"
    assert "multilingual-e5" in config["embedding_model"]
    assert not any(key in config for key in ("database_url", "embedding_cache", "api_key", "password"))
    assert client.put(path, headers=auth, json={"default_language": "ja"}).status_code == 200
    assert client.get(path).json()["default_language"] == "ja"
    assert client.get(f"/api/workspaces/{ws}").json()["default_language"] == "ja"
    assert client.put(path, headers=auth, json={"default_language": "fr"}).status_code == 422
    assert (
        client.put(path, headers=auth, json={"default_language": "en", "api_key": "fake"}).status_code == 422
    )
    for role, denied in [("operator", 403), ("viewer", 403), ("other", 404)]:
        auth = login(client, role)
        assert client.get(path).status_code == denied
        assert client.put(path, headers=auth, json={"default_language": "zh"}).status_code == denied


def test_usage_counts_unknowns_and_filters_workspace_and_time(system):
    ws, actor = system["workspace"], system["users"]["operator"].id
    with Session(system["engine"]) as db, db.begin():
        now = db.scalar(select(func.clock_timestamp()))

        def add(workspace, status, tokens, cost, duration, age, model="model-a"):
            db.add(
                ModelCall(
                    workspace_id=workspace,
                    actor_id=actor,
                    operation="embed_query",
                    provider="local_cpu",
                    model=model,
                    revision="test-revision",
                    status=status,
                    input_tokens=tokens,
                    api_cost_usd=cost,
                    duration_ms=duration,
                    created_at=now - timedelta(days=age),
                )
            )

        add(ws, "succeeded", 12, 0, 120, 0.5)
        add(ws, "failed", 4, None, 30, 2)
        add(ws, "uncertain", None, None, None, 3)
        add(ws, "started", None, None, None, 4)
        add(ws, "succeeded", 8, 0, 10, 30)
        add(ws, "succeeded", 1000, 50, 9000, 91)
        add(ws, "succeeded", 1000, 50, 9000, -1)
        add(system["foreign"], "succeeded", 99999, 99, 99999, 1, "foreign-secret-model")
    client = system["client"]
    login(client, "viewer")
    path = f"/api/workspaces/{ws}/usage"
    response = client.get(path)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["totals"] == {
        "calls": 4,
        "succeeded": 1,
        "failed": 1,
        "uncertain": 1,
        "started": 1,
        "input_tokens": 16,
        "output_tokens": 0,
        "missing_output_tokens": 0,
        "missing_tokens": 2,
        "recorded_cost_usd": 0,
        "missing_cost": 3,
        "recorded_duration_ms": 150,
        "missing_duration": 2,
    }
    assert len(data["models"]) == 1 and data["models"][0]["calls"] == 4
    assert "foreign-secret-model" not in response.text
    assert client.get(path, params={"days": 1}).json()["totals"]["calls"] == 1
    assert client.get(path, params={"days": 90}).json()["totals"]["calls"] == 5
    assert client.get(path, params={"days": 0}).status_code == 422
    assert client.get(path, params={"days": 91}).status_code == 422
    login(client, "other")
    assert client.get(path).status_code == 404


def test_usage_empty_and_model_output_bound_with_complete_totals(system):
    client, ws = system["client"], system["workspace"]
    login(client)
    path = f"/api/workspaces/{ws}/usage"
    empty = client.get(path).json()
    assert empty["totals"]["calls"] == 0 and empty["models"] == [] and not empty["more_models"]
    with Session(system["engine"]) as db, db.begin():
        for index in range(22):
            db.add(
                ModelCall(
                    workspace_id=ws,
                    actor_id=system["users"]["admin"].id,
                    operation="embed_query",
                    provider="local_cpu",
                    model=f"model-{index:02d}",
                    revision="r1",
                    status="succeeded",
                    input_tokens=2,
                    api_cost_usd=0,
                    duration_ms=3,
                )
            )
    report = client.get(path).json()
    assert report["totals"]["calls"] == 22 and report["totals"]["input_tokens"] == 44
    assert len(report["models"]) == 20 and report["more_models"]
    assert [row["model"] for row in report["models"]] == [f"model-{i:02d}" for i in range(20)]


def test_generation_groups_request_hashes_and_preserves_unknown_output(system):
    ws = system["workspace"]
    with Session(system["engine"]) as db, db.begin():
        for revision, tokens in [("request-a", 43), ("request-b", 41), ("request-c", None)]:
            db.add(
                ModelCall(
                    workspace_id=ws,
                    actor_id=system["users"]["admin"].id,
                    operation="generate",
                    provider="local_ollama",
                    model="qwen2.5:7b",
                    revision=revision,
                    status="succeeded",
                    output_tokens=tokens,
                )
            )
    login(system["client"])
    report = system["client"].get(f"/api/workspaces/{ws}/usage").json()
    assert len(report["models"]) == 1
    assert report["models"][0]["calls"] == 3
    assert report["totals"]["output_tokens"] == 84
    assert report["totals"]["missing_output_tokens"] == 1
