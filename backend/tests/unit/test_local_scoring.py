"""Local scoring cannot substitute human provenance or omit failed case denominators."""

import importlib.util
import json
import sys

import pytest

from tests.unit.test_generation_scoring import ROOT, fixture
from tests.unit.test_generation_scoring import scoring as shared

sys.modules.setdefault("generation_scoring", shared)
SPEC = importlib.util.spec_from_file_location("local_scoring", ROOT / "local_scoring.py")
scoring = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scoring)
PROTOCOL = json.loads((ROOT / "generation-review-local-v1.json").read_text(encoding="utf-8"))


def local_fixture():
    cases, report, judgments = fixture()
    report.update(experiment="local-generation-batch-v1", documents=[])
    report.update(
        status="snapshot_collected", runtime_after=report["runtime"], evidence_hash=shared.digest([])
    )
    for row in report["cases"]:
        for item in row["detail"]["pipelines"]:
            item["configuration"].update(transport="local_ollama", version=2, model="local-test")
            item.update(initial_response=None, outcome="set_aside")
    for row, group in zip(report["cases"], [judgments[i : i + 4] for i in range(0, 120, 4)], strict=True):
        for item, review in zip(row["detail"]["pipelines"], group, strict=True):
            review["observation_hash"] = shared.observation(row, item)
    return cases, report, judgments


def test_local_missing_baselines_remain_in_denominators(tmp_path):
    cases, report, judgments = local_fixture()
    result = scoring.score(report, cases, [], judgments, tmp_path, PROTOCOL)
    assert len(result["results"]) == 120
    for name, pipeline in result["pipelines"].items():
        assert pipeline["groups"]["all"]["total"] == 30
        assert pipeline["local_target_met"] is (name == "system_v1")


@pytest.mark.parametrize("problem", ["case", "mode", "review", "strategy", "status", "evidence"])
def test_local_changed_inputs_fail_closed(tmp_path, problem):
    cases, report, judgments = local_fixture()
    if problem == "case":
        report["cases"].pop()
    elif problem == "mode":
        report["experiment"] = "generation-batch-v1"
    elif problem == "review":
        judgments[0]["observation_hash"] = "changed"
    elif problem == "status":
        report["status"] = "collecting"
    elif problem == "evidence":
        report["evidence_hash"] = "changed"
    else:
        report["cases"][0]["detail"]["pipelines"][0]["configuration"]["strategy"] = "vector"
    with pytest.raises(ValueError):
        scoring.score(report, cases, [], judgments, tmp_path, PROTOCOL)
