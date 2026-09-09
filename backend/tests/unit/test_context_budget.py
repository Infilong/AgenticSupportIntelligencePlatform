import json

from app.modules.support.context import pack


def payload_size(context):
    return len(json.dumps(context, ensure_ascii=False).encode())


def test_oversized_middle_source_does_not_discard_later_evidence():
    rows = [{"text": "first"}, {"text": "方" * 8000}, {"text": "later fact"}]
    context = pack("question", "en", rows)
    assert context["sources"] == [rows[0], rows[2]]
    assert payload_size(context) <= 24000


def test_all_oversized_sources_are_omitted_whole():
    assert pack("question", "en", [{"text": "x" * 24000}] * 5)["sources"] == []


def test_exact_byte_limit_and_top_five_candidate_policy():
    empty = pack("question", "en", [{"text": ""}])
    row = {"text": "x" * (24000 - payload_size(empty))}
    context = pack("question", "en", [row])
    assert context["sources"] == [row]
    assert payload_size(context) == 24000
    assert pack("question", "en", [{"text": row["text"] + "x"}])["sources"] == []
    assert pack("question", "en", [{"text": "x" * 24000}] * 5 + [{"text": "sixth"}])["sources"] == []
