"""Evidence coverage must survive bounded ingestion work, not only retain valid offsets."""

import pytest

from app.modules.knowledge.splitting import split_document
from tests.unit.test_splitting import CharacterTokenizer


@pytest.mark.parametrize("prefix", ["x ", "方針", "政策"])
def test_artificial_block_boundary_preserves_identifier_and_fact(prefix):
    fact = "ERROR-8421 means contact support immediately."
    source = prefix * 3999 + fact
    passages = split_document(source, CharacterTokenizer())
    assert any(fact in passage.text for passage in passages)
    for passage in passages:
        assert source[passage.start : passage.end] == passage.text
        assert passage.token_count <= 359


def test_overlap_never_crosses_distinct_headings_with_the_same_title():
    source = "# Policy\n" + "first rule. " * 800 + "\n# Policy\nsecond rule only."
    passages = split_document(source, CharacterTokenizer())
    assert all(not ("first rule" in p.text and "second rule" in p.text) for p in passages)
    assert any("second rule only." in p.text for p in passages)


def test_multiple_work_boundaries_preserve_distinct_facts():
    source = "x " * 3999 + "ERROR-8421 requires escalation.\n"
    source += "方針" * ((15998 - len(source)) // 2)
    source += "期限は14日です。"
    passages = split_document(source, CharacterTokenizer())
    for fact in ("ERROR-8421 requires escalation.", "期限は14日です。"):
        assert any(fact in passage.text for passage in passages)
    assert all(source[p.start : p.end] == p.text for p in passages)


def test_sparse_document_keeps_bounded_tokenizer_work():
    class WordTokenizer:
        longest = 0

        def token_count(self, text):
            self.longest = max(self.longest, len(text))
            return len(text.split()) + 2

    provider = WordTokenizer()
    source = ("x" + " " * 7999) * 12
    passages = split_document(source, provider)
    assert provider.longest <= 16000
    assert all(source[p.start : p.end] == p.text for p in passages)


def test_replaced_tail_does_not_bypass_chunk_limit():
    with pytest.raises(ValueError, match="1000 chunks"):
        split_document("方針" * 180000, CharacterTokenizer())
