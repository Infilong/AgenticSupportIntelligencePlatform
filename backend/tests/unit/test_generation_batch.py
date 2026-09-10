"""Frozen denominators, idempotent recovery and blind generation exports."""

import importlib.util
import json
from pathlib import Path

import httpx
import pytest

SOURCE = Path(__file__).resolve().parents[3] / "evals/generation_batch.py"
SPEC = importlib.util.spec_from_file_location("generation_batch", SOURCE)
batch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(batch)


def rows():
    return batch.case_rows(
        [
            {
                "id": f"{language}{i}",
                "language": language,
                "question": f"Question {i}",
                "expected_facts": ["NEVER SEND THIS"],
            }
            for language in ("en", "ja", "zh")
            for i in range(10)
        ]
    )


def detail(row):
    return {
        "id": row["comparison_id"],
        "question": row["question"],
        "language": row["language"],
        "corpus_hash": "frozen",
        "comparable": True,
        "pipelines": [
            {
                "name": name,
                "state": "waiting_for_input",
                "configuration": {
                    "strategy": strategy,
                    "limit": 5,
                    "context_bytes": 24000,
                    "transport": "attributed_development",
                    "version": 1,
                },
            }
            for name, strategy in zip(batch.PIPELINES, (None, "vector", "hybrid", "hybrid"))
        ],
    }


def test_failed_admission_retains_denominators_and_retry_key(tmp_path):
    report = {"cases": rows(), "workspaces": {"primary": "workspace"}}
    keys = []

    def denied(request):
        assert request.method == "POST"
        assert set(json.loads(request.content)) == {"original", "language"}
        assert b"NEVER SEND" not in request.content
        keys.append(request.headers["Idempotency-Key"])
        return httpx.Response(503, json={"detail": "Unavailable"})

    with httpx.Client(base_url="http://local", transport=httpx.MockTransport(denied)) as client:
        assert not batch.collect(client, report, tmp_path)
        assert not batch.collect(client, report, tmp_path)
    assert keys[:30] == keys[30:]
    for language, denominator in (("all", 30), ("en", 10), ("ja", 10), ("zh", 10)):
        result = report["summary"][language]
        assert result["denominator"] == result["collection_errors"] == denominator
        assert all(states == {"not_observed": denominator} for states in result["pipelines"].values())
    assert all(len(row["failures"]) == 2 for row in report["cases"])


def test_resume_keeps_admitted_id_and_original_export(tmp_path):
    row = rows()[0]
    row["comparison_id"] = "admitted"
    report = {"cases": [row], "workspaces": {"primary": "workspace"}}
    request_body = {
        "generation_request": {"messages": []},
        "request_hash": "original",
        "context_hash": "context",
    }

    def handle(request):
        assert request.method == "GET"  # Already admitted; no duplicate POST.
        return httpx.Response(
            200, json=request_body if request.url.path.endswith("/request") else detail(row)
        )

    with httpx.Client(base_url="http://local", transport=httpx.MockTransport(handle)) as client:
        assert batch.collect(client, report, tmp_path)
        original = (tmp_path / "requests/en0/direct_llm.json").read_bytes()
        request_body["request_hash"] = "changed"
        assert not batch.collect(client, report, tmp_path)
    assert (tmp_path / "requests/en0/direct_llm.json").read_bytes() == original
    assert "Prepared request changed" in row["error"]["message"]


@pytest.mark.parametrize("change", ["identity", "corpus", "config", "missing"])
def test_rejects_noncomparable_or_changed_contract(change):
    row = rows()[0]
    row["comparison_id"] = "admitted"
    value = detail(row)
    if change == "identity":
        value["question"] = "Different question"
    elif change == "corpus":
        value["comparable"] = False
    elif change == "config":
        value["pipelines"][0]["configuration"]["limit"] = 20
    else:
        value["pipelines"].pop()
    with pytest.raises(ValueError):
        batch.validate_detail(row, value, "frozen")


def test_interrupted_export_recovers_without_duplicate_admission(tmp_path, monkeypatch):
    row = rows()[0]
    row["comparison_id"] = "admitted"
    key = row["key"]
    report = {"cases": [row], "workspaces": {"primary": "workspace"}}
    original_write = Path.write_text
    interrupted = False

    def write(path, data, **kwargs):
        nonlocal interrupted
        if path.name == "direct_llm.tmp" and not interrupted:
            interrupted = True
            original_write(path, "{", **kwargs)
            raise OSError("Injected interrupted write")
        return original_write(path, data, **kwargs)

    def handle(request):
        assert request.method == "GET"
        return httpx.Response(
            200, json={"request_hash": "same"} if request.url.path.endswith("/request") else detail(row)
        )

    monkeypatch.setattr(Path, "write_text", write)
    with httpx.Client(base_url="http://local", transport=httpx.MockTransport(handle)) as client:
        assert not batch.collect(client, report, tmp_path)
        assert not (tmp_path / "requests/en0/direct_llm.json").exists()
        assert batch.collect(client, report, tmp_path)
    assert row["key"] == key
    assert len(row["failures"]) == 1
    assert json.loads((tmp_path / "requests/en0/direct_llm.json").read_text()) == {"request_hash": "same"}
