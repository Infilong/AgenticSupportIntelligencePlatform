import json
from dataclasses import replace

import pytest

from app.core.language import SupportedLanguage
from app.services.evaluation_case_identity import case_fingerprint
from app.services.evaluation_loader import LoadedEvaluationCase
from tests.test_evaluations import auth_headers, create_workspace, login, register


@pytest.mark.parametrize("change", ["input", "expectation", "duplicate", "reorder"])
def test_comparison_requires_the_same_case_multiset(client, change):
    register(client, "case-identity@example.test")
    token = login(client, "case-identity@example.test")
    workspace = create_workspace(client, token)
    cases = [{"id": "one", "language": "en", "input_message": "Refund policy?"},
             {"id": "two", "language": "en", "input_message": "Shipping policy?"}]

    def run(rows):
        response = client.post(f"/api/v1/workspaces/{workspace['id']}/evaluations",
                               headers=auth_headers(token), json={
            "name": "Identity", "modes": ["direct_llm"],
            "jsonl_cases": "\n".join(json.dumps(row) for row in rows),
        })
        assert response.status_code == 201
        return response.json()["run"]

    baseline = run(cases)
    changed = [dict(case) for case in cases]
    if change == "input":
        changed[0]["input_message"] = "A different question"
    elif change == "expectation":
        changed[0]["max_prompt_tokens"] = 0
    elif change == "duplicate":
        changed.append(dict(changed[0]))
    else:
        changed.reverse()
    current = run(changed)
    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/evaluations/{current['id']}/compare/{baseline['id']}",
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    rows = response.json()["deltas"]
    assert rows
    if change == "reorder":
        assert all(row["direction"] != "incomparable" for row in rows)
    else:
        assert all(row["direction"] == "incomparable" and row["delta"] is None for row in rows)


def test_fingerprint_is_stable_for_metadata_key_order_but_preserves_case_fields():
    case = LoadedEvaluationCase("one", SupportedLanguage.en, "Question",
                                metadata={"a": 1, "b": 2})
    original = case_fingerprint(case)
    assert original == case_fingerprint(replace(case, metadata={"b": 2, "a": 1}))
    for updates in ({"language": SupportedLanguage.ja}, {"expected_route": "human_review"},
                    {"expected_tool_calls": ["search_documents"]}, {"max_prompt_tokens": 0},
                    {"must_include": ["refund"]}, {"expected_sources": ["policy"]},
                    {"metadata": {"a": 2}}):
        assert original != case_fingerprint(replace(case, **updates))
