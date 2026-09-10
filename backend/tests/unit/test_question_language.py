import pytest
from pydantic import ValidationError

from app.modules.comparisons.schemas import ComparisonInput
from app.modules.conversations.schemas import ImportRow
from app.modules.support.language import question_language


@pytest.mark.parametrize(
    "text,expected",
    [
        ("删除账户确认", "zh"),
        ("Team方案有多少成员？", "zh"),
        ("アカウント削除の確認期限は？", "ja"),
        ("When is deletion confirmed?", "en"),
        ("。", "ja"),
    ],
)
def test_question_language_overrides_workspace_fallback(text, expected):
    assert question_language(text, "ja") == expected


@pytest.mark.parametrize("schema", [ComparisonInput, ImportRow])
@pytest.mark.parametrize("language", [None, "auto"])
def test_explicit_import_and_comparison_contracts_remain_required(schema, language):
    payload = {"original": "Question"}
    if language is not None:
        payload["language"] = language
    with pytest.raises(ValidationError):
        schema.model_validate(payload)
