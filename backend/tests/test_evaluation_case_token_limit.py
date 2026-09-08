import json

import pytest
from sqlalchemy import func, select

from app.core.language import SupportedLanguage
from app.models.agent import AgentConfig
from app.models.ai import AIRun
from app.models.evaluation import EvaluationCase, EvaluationRun
from app.services.evaluation_loader import (
    EvaluationCaseLoadError,
    LoadedEvaluationCase,
    load_jsonl_cases,
)
from app.services.evaluation_scoring import _score_case
from tests.test_evaluations import auth_headers, create_workspace, login, register


@pytest.mark.parametrize("limit,usage,expected", [
    (None, 100, None), (0, 0, 1.0), (10, 10, 1.0), (10, 11, 0.0), (10, None, 0.0),
])
def test_case_limit_checks_measured_usage(limit, usage, expected):
    case = LoadedEvaluationCase("limit", SupportedLanguage.en, "Question",
                                max_prompt_tokens=limit)
    scores = _score_case(loaded_case=case, actual_route="human_review", answer=None,
                         citations=[], actual_tool_calls=[], actual_guardrail_failures=[],
                         prompt_tokens=usage)
    assert scores["prompt_token_limit_match"] == expected


@pytest.mark.parametrize("limit", [-1, True, False, 1.5, "100", [], {}, 2147483648])
def test_invalid_case_limits_are_rejected(limit):
    with pytest.raises(EvaluationCaseLoadError, match="max_prompt_tokens"):
        load_jsonl_cases(json.dumps({"id": "bad", "language": "en", "input_message": "Q",
                                    "max_prompt_tokens": limit}))


@pytest.mark.parametrize("mode", ["direct_llm", "vector_rag", "system_v1"])
def test_api_reports_case_limit_score(client, mode):
    from tests.test_evaluations import upload_refund_documents

    register(client, "case-limit@example.test")
    token = login(client, "case-limit@example.test")
    workspace = create_workspace(client, token)
    upload_refund_documents(client, token, workspace["id"])
    response = client.post(f"/api/v1/workspaces/{workspace['id']}/evaluations",
                           headers=auth_headers(token), json={
        "name": "Limit", "modes": [mode], "jsonl_cases": json.dumps({
            "id": "limit", "language": "en", "input_message": "What is the refund policy?",
            "max_prompt_tokens": 0,
        }),
    })
    assert response.status_code == 201
    result = response.json()["results"][0]
    assert result["prompt_tokens"] > 0
    assert json.loads(result["scores_json"])["prompt_token_limit_match"] == 0.0
    assert result["passed"] is False


@pytest.mark.parametrize("limit", [-1, True, "100"])
def test_invalid_later_case_leaves_no_execution_or_records(client, db_session, limit):
    register(client, "invalid-limit@example.test")
    token = login(client, "invalid-limit@example.test")
    workspace = create_workspace(client, token)
    models = (EvaluationRun, EvaluationCase, AIRun, AgentConfig)
    before = [db_session.scalar(select(func.count()).select_from(model)) for model in models]
    cases = [{"id": "good", "language": "en", "input_message": "Question"},
             {"id": "bad", "language": "en", "input_message": "Question",
              "max_prompt_tokens": limit}]
    response = client.post(f"/api/v1/workspaces/{workspace['id']}/evaluations",
                           headers=auth_headers(token), json={
        "name": "Rejected", "modes": ["system_v1"],
        "jsonl_cases": "\n".join(json.dumps(case) for case in cases),
    })
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "evaluation_case_load_failed"
    assert "max_prompt_tokens" in response.json()["detail"]["message"]
    assert "line 2" in response.json()["detail"]["message"]
    assert [db_session.scalar(select(func.count()).select_from(model))
            for model in models] == before
