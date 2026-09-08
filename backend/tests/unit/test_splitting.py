import pytest

from app.modules.knowledge.splitting import split_document


class CharacterTokenizer:
    def token_count(self, text):
        return len(text)


@pytest.mark.parametrize(
    "sentence",
    ["Policy applies to all employees. ", "全社員に適用される方針です。", "此政策适用于所有员工。"],
)
def test_long_sections_preserve_exact_spans_and_heading(sentence):
    body = sentence * 600
    source = "# First\n" + body + "\n# Second\n" + body
    passages = split_document(source, CharacterTokenizer())
    assert len(passages) > 20
    second = source.index("# Second")
    assert any(p.section == "Second" for p in passages)
    for passage in passages:
        assert source[passage.start : passage.end] == passage.text
        assert passage.section == ("First" if passage.start < second else "Second")
        assert passage.token_count <= 359


def test_cancellation_between_bounded_blocks():
    checks = 0

    def checkpoint():
        nonlocal checks
        checks += 1
        if checks == 2:
            raise InterruptedError("cancelled")

    with pytest.raises(InterruptedError):
        split_document("policy text. " * 2000, CharacterTokenizer(), checkpoint)
    assert checks == 2


def test_opaque_token_rejected_before_tokenizer():
    class MustNotLoad:
        def token_count(self, text):
            raise AssertionError("Tokenizer must not run")

    with pytest.raises(ValueError, match="unbroken"):
        split_document("a" * 4097, MustNotLoad())
