import pytest

from app.core.language import SupportedLanguage
from app.services.mock_support_answer import MAX_EXCERPT_CHARS, mock_support_answer


@pytest.mark.parametrize("language,policy,wrong,label", [
    ("en", "Refunds within 7 days require an active account.", "30 days", "Mock response"),
    ("ja", "返金は7日以内で、有効なアカウントが必要です。", "30日", "模擬応答"),
    ("zh", "退款须在7天内申请，且账号必须正常。", "30天", "模拟回答"),
])
def test_mock_quotes_policy_and_conditions_without_inventing_exceptions(
    language, policy, wrong, label,
):
    citation = "[Policy v2 / chunk 1]"
    answer = mock_support_answer(
        language=SupportedLanguage(language), intent="refund_request",
        input_message="Allow a partial refund for a duplicate enterprise upgrade after 30 days",
        chunks=[{"content": policy, "citation": citation}],
    )
    assert policy in answer
    assert citation in answer
    assert label in answer
    assert wrong not in answer
    assert "partial refund" not in answer


@pytest.mark.parametrize("language", list(SupportedLanguage))
def test_missing_citable_evidence_never_becomes_a_policy(language):
    empty = mock_support_answer(
        language=language, intent="refund_request", input_message="Refund within 30 days?",
        chunks=[],
    )
    invalid = mock_support_answer(
        language=language, intent="refund_request", input_message="Refund within 30 days?",
        chunks=[{"content": "Refund within 30 days"}, {"citation": "[empty]"}],
    )
    assert empty == invalid
    assert "30" not in empty
    assert empty


def test_excerpt_is_bounded_and_does_not_copy_later_chunks():
    answer = mock_support_answer(
        language=SupportedLanguage.en, intent=None, input_message="ignored",
        chunks=[{"content": "a" * 5000, "citation": "[first]"},
                {"content": "MUST NOT APPEAR", "citation": "[second]"}],
    )
    assert "a" * MAX_EXCERPT_CHARS + "…\n[first]" in answer
    assert "a" * (MAX_EXCERPT_CHARS + 1) not in answer
    assert "MUST NOT APPEAR" not in answer
    assert "[second]" not in answer
