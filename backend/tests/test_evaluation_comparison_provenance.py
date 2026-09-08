import json
from types import SimpleNamespace
from uuid import UUID

import pytest
from sqlalchemy import select

from app.models.evaluation import EvaluationResult
from app.services.evaluation_comparison import compare_metrics
from app.services.evaluation_scoring import EVALUATION_CONTRACT
from tests.test_evaluations import (
    auth_headers,
    create_workspace,
    login,
    register,
    run_simple_evaluation,
)


@pytest.mark.parametrize("version", [None, "future-contract"])
def test_comparison_refuses_unknown_or_different_contract(client, db_session, version):
    register(client, "comparison-provenance@example.test")
    token = login(client, "comparison-provenance@example.test")
    workspace = create_workspace(client, token)
    baseline = run_simple_evaluation(client, token, workspace["id"], "Baseline")
    current = run_simple_evaluation(client, token, workspace["id"], "Current")
    for result in db_session.scalars(select(EvaluationResult).where(
        EvaluationResult.evaluation_run_id == UUID(baseline["id"])
    )):
        scores = json.loads(result.scores_json)
        if version is None:
            scores.pop("evaluation_contract", None)
        else:
            scores["evaluation_contract"] = version
        result.scores_json = json.dumps(scores)
    db_session.commit()
    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/evaluations/{current['id']}/compare/{baseline['id']}",
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["deltas"]
    assert all(row["direction"] == "incomparable" and row["delta"] is None
               for row in body["deltas"])
    assert body["improvement_count"] == body["regression_count"] == 0
    assert all(row["current_value"] is not None and row["baseline_value"] is not None
               for row in body["deltas"])


@pytest.mark.parametrize("versions", [[], [None], [EVALUATION_CONTRACT, None],
                                    [EVALUATION_CONTRACT, "future-contract"]])
def test_empty_unknown_or_mixed_group_cannot_prove_compatibility(versions):
    def run(contracts):
        return SimpleNamespace(
            results=[SimpleNamespace(mode="system_v1", language="en",
                                     scores_json=json.dumps({"evaluation_contract": version,
                                         "evaluation_case_fingerprint": "a" * 64}))
                     for version in contracts],
            metrics=[SimpleNamespace(mode="system_v1", language="en",
                                     metric_name="case_pass_rate", metric_value=1.0)],
        )
    delta = compare_metrics(run([EVALUATION_CONTRACT]), run(versions))[0]
    assert delta["direction"] == "incomparable"
    assert delta["delta"] is None


def test_contracts_are_grouped_by_mode_and_language():
    def run(legacy):
        return SimpleNamespace(
            results=[SimpleNamespace(mode="system_v1", language=language,
                                     scores_json=json.dumps({
                                         "evaluation_case_fingerprint": "a" * 64,
                                         "evaluation_contract":
                                         None if language == legacy else EVALUATION_CONTRACT}))
                     for language in ("en", "ja")],
            metrics=[SimpleNamespace(mode="system_v1", language=language,
                                     metric_name="case_pass_rate", metric_value=1.0)
                     for language in ("en", "ja")],
        )
    deltas = compare_metrics(run(None), run("ja"))
    assert {row["language"]: row["direction"] for row in deltas} == {
        "en": "unchanged", "ja": "incomparable",
    }
