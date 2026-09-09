import json
import uuid

import pytest

from app.modules.evaluations.projection import project
from tests.evaluation_fixture import report


def test_recomputes_metrics_preserves_failures_and_exclusions_without_raw_metadata():
    data = report(uuid.uuid4())
    _, snapshot, traces = project(json.dumps(data).encode())
    vector = snapshot.strategies[0]
    assert vector.scores["all"].passed == 25
    assert vector.scores["all"].total == 26
    assert vector.scores["all"].total_groups == 27
    assert vector.measured_requests == 30
    assert vector.warm_p95_seconds == 1.9
    assert vector.scores["ja"].passed == 8
    assert [case.id for case in vector.cases if case.passed is False] == ["ja1"]
    assert sum(case.passed is None for case in vector.cases) == 4
    assert snapshot.generation == "not_verified"
    assert len(traces) == 160
    assert "DO_NOT_EXPOSE" not in snapshot.model_dump_json()
    assert "untrusted_aggregate" not in snapshot.model_dump_json()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda data: data.update(status="started"),
        lambda data: data.update(experiment_valid=False),
        lambda data: data.update(generation="verified"),
        lambda data: data["strategies"]["vector"]["cases"].pop(),
        lambda data: data["strategies"]["vector"]["cases"][0].update(elapsed_seconds=float("nan")),
        lambda data: data["strategies"]["vector"]["cases"][0].update(groups_found=7),
        lambda data: data["strategies"]["vector"]["cases"][0].update(retrieval_passed=None),
        lambda data: data["strategies"]["vector"]["cases"][0].update(id="different-case"),
        lambda data: data["strategies"]["vector"]["cases"][0].update(fact_results=[False]),
        lambda data: data["strategies"]["vector"]["cases"][0].update(leakage=["foreign"]),
    ],
)
def test_rejects_partial_or_inconsistent_evidence(mutation):
    data = report(uuid.uuid4())
    mutation(data)
    with pytest.raises(ValueError):
        project(json.dumps(data).encode())


def test_failed_safety_is_retained_not_promoted_to_pass():
    data = report(uuid.uuid4())
    data["strategies"]["vector"]["negative_probes"][0]["leakage"] = ["private-id"]
    _, snapshot, _ = project(json.dumps(data).encode())
    assert not snapshot.strategies[0].safety_passed
    assert not snapshot.strategies[0].retrieval_gate_passed
    assert "private-id" not in snapshot.model_dump_json()


def test_failed_fact_with_complete_sections_is_a_failed_case():
    data = report(uuid.uuid4())
    data["strategies"]["vector"]["cases"][0].update(fact_results=[False], retrieval_passed=False)
    _, snapshot, _ = project(json.dumps(data).encode())
    assert snapshot.strategies[0].scores["en"].passed == 7
    assert snapshot.strategies[0].scores["en"].groups_found == 8
