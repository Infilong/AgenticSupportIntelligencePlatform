"""Scoring must not turn stale, missing or structurally invalid evidence into a pass."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3] / "evals"
SPEC = importlib.util.spec_from_file_location("generation_scoring", ROOT / "generation_scoring.py")
scoring = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scoring)
PROTOCOL = json.loads((ROOT / "generation-review-v1.json").read_text())


def fixture():
    cases = [
        {"id": f"{lang}{i}", "language": lang, "question": "Question"}
        for lang in ("en", "ja", "zh")
        for i in range(10)
    ]
    rows = []
    for case in cases:
        rows.append(
            {
                **case,
                "comparison_id": case["id"],
                "error": None,
                "detail": {
                    "id": case["id"],
                    "question": "Question",
                    "language": case["language"],
                    "corpus_hash": "frozen",
                    "comparable": True,
                    "pipelines": [
                        {
                            "name": name,
                            "state": "completed",
                            "outcome": "clarification_needed",
                            "configuration": {
                                "strategy": {
                                    "direct_llm": None,
                                    "vector_rag": "vector",
                                    "hybrid_rag": "hybrid",
                                    "system_v1": "hybrid",
                                }[name],
                                "limit": 5,
                                "context_bytes": 24000,
                                "transport": "attributed_development",
                                "version": 1,
                            },
                        }
                        for name in scoring.PIPELINES
                    ],
                },
            }
        )
    report = {
        "cases": rows,
        "corpus_hash": "frozen",
        "experiment": "generation-batch-v1",
        "status": "snapshot_collected",
        "corpus_ready": True,
        "runtime": {"api": {}, "worker": {}},
    }
    judgments = [
        {
            "case_id": row["id"],
            "pipeline": item["name"],
            "observation_hash": scoring.observation(row, item),
            "reviewer": "Independent tester",
            "kind": "human",
            "rationale": "Synthetic early-routing judgment for this test only.",
            "checks": {name: True for name in PROTOCOL["checks"]},
        }
        for row in rows
        for item in row["detail"]["pipelines"]
    ]
    return cases, report, judgments


def test_missing_judgments_stay_in_fixed_denominators(tmp_path):
    cases, report, _ = fixture()
    result = scoring.score(report, cases, [], {}, [], tmp_path, PROTOCOL)
    assert len(result["results"]) == 120
    assert all(not item["development_target_met"] for item in result["pipelines"].values())
    for pipeline in result["pipelines"].values():
        assert pipeline["groups"]["all"] == {"total": 30, "reviewed": 0, "passed": 0}
        assert pipeline["groups"]["ja"]["total"] == 10


def test_stale_or_duplicate_review_is_rejected(tmp_path):
    cases, report, judgments = fixture()
    with pytest.raises(ValueError, match="Duplicate"):
        scoring.score(report, cases, [*judgments, judgments[0]], {}, [], tmp_path, PROTOCOL)
    report["cases"][0]["detail"]["pipelines"][0]["state"] = "failed"
    with pytest.raises(ValueError, match="different observation"):
        scoring.score(report, cases, judgments, {}, [], tmp_path, PROTOCOL)


def test_safety_failure_cannot_hide_in_high_aggregate(tmp_path):
    cases, report, judgments = fixture()
    judgments[3]["checks"]["no_unsafe_claims"] = False
    result = scoring.score(report, cases, judgments, {}, [], tmp_path, PROTOCOL)
    direct = result["pipelines"]["system_v1"]
    assert direct["groups"]["all"]["passed"] == 29
    assert not direct["development_target_met"]
    assert result["live_generation_quality"] == "not_verified"


def test_collection_failure_cannot_reuse_passing_observation(tmp_path):
    cases, report, judgments = fixture()
    report["cases"][0]["error"] = {"message": "403 denied"}
    result = scoring.score(report, cases, judgments, {}, [], tmp_path, PROTOCOL)
    assert all(not item["development_target_met"] for item in result["pipelines"].values())
    assert result["pipelines"]["system_v1"]["groups"]["all"]["reviewed"] == 29


@pytest.mark.parametrize("change", ["status", "configuration"])
def test_invalid_run_envelope_or_strategy_cannot_pass(tmp_path, change):
    cases, report, judgments = fixture()
    assert scoring.score(report, cases, judgments, {}, [], tmp_path, PROTOCOL)["pipelines"]["system_v1"][
        "development_target_met"
    ]
    if change == "status":
        report["status"] = "failed"
    else:
        report["cases"][0]["detail"]["pipelines"][3]["configuration"]["strategy"] = "vector"
    with pytest.raises(ValueError):
        scoring.score(report, cases, judgments, {}, [], tmp_path, PROTOCOL)


def response_fixture(tmp_path):
    import hashlib

    text = "The deadline is fourteen days."
    (tmp_path / "policy.txt").write_text(text)
    source = {
        "chunk_id": "chunk",
        "version_id": "version",
        "document_id": "document",
        "checksum": hashlib.sha256(text.encode()).hexdigest(),
        "start_offset": 0,
        "end_offset": len(text),
        "text": text,
    }
    generation = {
        "messages": [
            {"role": "system", "content": "Use sources"},
            {"role": "user", "content": json.dumps({"sources": [source]})},
        ]
    }
    request = {
        "generation_request": generation,
        "request_hash": scoring.digest(generation),
        "context_hash": "context",
    }
    response = {
        "answer": "Fourteen days.",
        "request_hash": request["request_hash"],
        "context_hash": "context",
        "citations": [{"chunk_id": "chunk", "quote": "fourteen days"}],
    }
    item = {
        "name": "vector_rag",
        "request_hash": request["request_hash"],
        "initial_response": response,
        "contributor_id": "contributor",
        "response_hash": scoring.digest({"contributor": "contributor", "response": response}),
    }
    documents = [
        {
            "version_id": "version",
            "document_id": "document",
            "spec": {"state": "active", "path": "policy.txt"},
        }
    ]
    return item, request, documents


@pytest.mark.parametrize(
    "change,expected",
    [
        ("quote", "invalid_citation"),
        ("version", "ineligible_source"),
        ("text", "source_identity"),
        ("response", "response_identity"),
    ],
)
def test_source_bound_citation_and_response_integrity(tmp_path, change, expected):
    item, request, documents = response_fixture(tmp_path)
    assert scoring.evidence(item, request, documents, tmp_path) == []
    if change == "quote":
        item["initial_response"]["citations"][0]["quote"] = "thirty days"
    elif change == "version":
        documents[0]["spec"]["state"] = "foreign"
    elif change == "text":
        (tmp_path / "policy.txt").write_text("An altered source")
    else:
        item["initial_response"]["answer"] = "Altered answer"
    assert expected in scoring.evidence(item, request, documents, tmp_path)
