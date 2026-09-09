"""Known positions are stronger evidence than an ambiguous substring match."""

import pytest
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.modules.knowledge.span_splitter import SEPARATORS, SpanSplitter
from app.modules.knowledge.splitting import split_document
from tests.unit.test_splitting import CharacterTokenizer


@pytest.mark.parametrize("source,second", [("abc " * 2000, 304), ("方" * 8000, 305)], ids=["english", "cjk"])
def test_repetition_records_the_actual_overlapping_occurrence(source, second):
    passages = split_document(source, CharacterTokenizer())
    assert passages[0].start == 0
    assert passages[1].start == second
    assert passages[-1].end == len(source.rstrip())
    for previous, current in zip(passages, passages[1:]):
        assert current.start > previous.start
        assert current.end > previous.end
        assert not source[previous.end : current.start].strip()


def test_repeated_work_blocks_cover_the_entire_document():
    source = "abc " * 6000
    passages = split_document(source, CharacterTokenizer())
    assert passages[-1].end == len(source.rstrip())
    covered = set()
    for passage in passages:
        assert source[passage.start : passage.end] == passage.text
        covered.update(range(passage.start, passage.end))
    assert all(index in covered for index, char in enumerate(source) if not char.isspace())


@pytest.mark.parametrize(
    "source",
    [
        "  policy rule. " * 200 + "\n\nfinal rule.\n",
        "　方針です。例外！条件？\n" * 150,
        "规则，条件、例外。\n" * 150,
        "abc " * 1000,
        "x" * 1000,
        "\n \t " * 1000,
        "",
    ],
    ids=["english", "japanese", "chinese", "repetition", "recursive", "whitespace", "empty"],
)
def test_adapter_preserves_langchain_chunk_text(source):
    vanilla = RecursiveCharacterTextSplitter(
        chunk_size=350,
        chunk_overlap=45,
        keep_separator="end",
        length_function=len,
        separators=SEPARATORS,
    )
    spans = SpanSplitter(len).split_text(source)
    assert [str(span) for span in spans] == vanilla.split_text(source)
    assert all(source[span.start : span.end] == span for span in spans)


def test_trimmed_leading_whitespace_preserves_position():
    spans = SpanSplitter(len).split_text("   first policy\n\n  second policy  ")
    assert spans[0].start == 3
    assert spans[0].end == len("   first policy\n\n  second policy")


def test_tokenizer_overhead_and_repetition_match_langchain():
    def word_tokens(text):
        return len(text.split()) + 2

    source = "  policy applies. " * 1000 + "\n\nFinal exception."
    vanilla = RecursiveCharacterTextSplitter(
        chunk_size=350,
        chunk_overlap=45,
        keep_separator="end",
        length_function=word_tokens,
        separators=SEPARATORS,
    )
    spans = SpanSplitter(word_tokens).split_text(source)
    assert [str(span) for span in spans] == vanilla.split_text(source)
    assert spans[0].start == 2
    assert spans[-1].end == len(source)
    assert all(source[span.start : span.end] == span for span in spans)
    assert all(a.start < b.start for a, b in zip(spans, spans[1:]))
    assert all(word_tokens(span) <= 350 for span in spans)
