import pytest

from app.providers.response_routing import route


@pytest.mark.parametrize(
    "question",
    [
        "Please refund my renewal",
        "请帮我退款",
        "私の契約を返金してください",
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
