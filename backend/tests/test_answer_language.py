import pytest

from app.core.language import SupportedLanguage
from app.services.evaluation_loader import LoadedEvaluationCase
from app.services.evaluation_runner import _score_case
from app.services.guardrails import evaluate_guardrails


@pytest.mark.parametrize("language,answer,citation,passed", [
    ("en", "Refunds are available within seven days. 返金について v1#chunk-0",
     "返金について v1#chunk-0", True),
    ("zh", "购买后七天内可以申请退款。 返金について v1#chunk-0",
     "返金について v1#chunk-0", True),
    ("ja", "購入から七日以内に返金できます。 退款政策 v1#chunk-0",
     "退款政策 v1#chunk-0", True),
    ("ja", "Refunds are available within seven days. 返金について v1#chunk-0",
     "返金について v1#chunk-0", False),
    ("ja", "返金について v1#chunk-0", "返金について v1#chunk-0", False),
    ("en", "Refunds are available. 別の情報 v1#chunk-9", "Policy v1#chunk-0", False),
])
@pytest.mark.parametrize("boundary", ["guardrail", "evaluation"])
def test_language_checks_answer_prose_not_citation_titles(
    language, answer, citation, passed, boundary,
):
    if boundary == "guardrail":
        decisions = evaluate_guardrails({
            "input_message": "Refund?", "detected_language": language,
            "draft_answer": answer, "packed_context_chunks": [
                {"citation": citation, "content": "Source policy"},
            ],
        })
        actual = next(item.passed for item in decisions
                      if item.guardrail_type == "language_preservation")
    else:
        case = LoadedEvaluationCase("language", SupportedLanguage(language), "Refund?")
        scores = _score_case(loaded_case=case, actual_route="finalize", answer=answer,
                            citations=[citation], actual_tool_calls=[],
                            actual_guardrail_failures=[])
        actual = scores["language_preserved"] == 1.0
    assert actual is passed


@pytest.mark.parametrize("content", [None, "", 7])
def test_invalid_packed_content_does_not_hide_citation_language(content):
    decisions = evaluate_guardrails({
        "detected_language": "en", "draft_answer": "Refund available. 返金について v1#chunk-0",
        "packed_context_chunks": [{"citation": "返金について v1#chunk-0", "content": content}],
    })
    assert not next(item.passed for item in decisions
                    if item.guardrail_type == "language_preservation")
