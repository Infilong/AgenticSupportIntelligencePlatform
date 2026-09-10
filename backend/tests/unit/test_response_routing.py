import pytest

from app.providers.response_routing import route


@pytest.mark.parametrize(
    "question",
    [
        "Please refund my renewal",
        "请帮我退款",
        "私の契約を返金してください",
        "请删除账户",
        "Please delete the account",
    ],
)
def test_sensitive_personal_request_cannot_auto_answer(question):
    assert route("answer", "Supported", {"original": question}, [1])["decision"] == "review"


def test_evidence_and_reason_are_required():
    assert route("answer", "", {}, [1])["decision"] == "review"
    assert route("answer", "Supported", {}, [])["decision"] == "missing"
    assert route("irrelevant", "Unrelated", {}, [1])["decision"] == "review"
    assert (
        route("answer", "Explicit plan limits", {"original": "Team plan limits?"}, [1])["decision"]
        == "answer"
    )


@pytest.mark.parametrize(
    "language,question",
    [
        ("zh", "完整的账户删除请求应在几个工作日内确认？"),
        ("zh", "账户删除申请的状态更新需要多少天？"),
        ("en", "Please explain the refund deadline."),
        ("ja", "返金の期限を教えてください。"),
    ],
)
def test_polite_policy_question_is_not_a_personal_action(language, question):
    assert (
        route("answer", "Supported", {"original": question, "language": language}, [1])["decision"]
        == "answer"
    )
