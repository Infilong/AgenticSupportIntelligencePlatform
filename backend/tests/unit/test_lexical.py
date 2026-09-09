import pytest

from app.modules.knowledge.fusion import fuse
from app.modules.knowledge.lexical import LexicalQueryTooLong, frequencies, query_terms


def test_unicode_identifiers_counts_and_unchanged_original():
    original = "ＥＲＲＯＲ－８４２２ error-8422 x_x ｶﾀｶﾅ 方 政策政策"
    counts = frequencies(original)
    assert counts == {
        "error-8422": 2,
        "error": 2,
        "8422": 2,
        "x_x": 1,
        "x": 2,
        "カタ": 1,
        "タカ": 1,
        "カナ": 1,
        "方": 1,
        "政策": 2,
        "策政": 1,
    }
    assert original.startswith("ＥＲＲＯＲ")
    assert frequencies("…！　") == {}
    assert query_terms("refund refund") == ["refund"]


def test_query_terms_reject_over_budget_without_silent_truncation():
    with pytest.raises(LexicalQueryTooLong, match="128"):
        query_terms(" ".join(f"word{i}" for i in range(129)))
    assert len(query_terms(" ".join(f"word{i}" for i in range(128)))) == 128
    with pytest.raises(LexicalQueryTooLong):
        query_terms("".join(chr(0x4E00 + i) for i in range(130)))


def test_fusion_preserves_raw_scores_and_absent_branch_rank():
    result = fuse(
        [{"chunk_id": "b", "cosine_similarity": 0.9}, {"chunk_id": "a", "cosine_similarity": 0.8}],
        [{"chunk_id": "c", "bm25_score": 2.5}, {"chunk_id": "b", "bm25_score": 1.5}],
    )
    assert [row["chunk_id"] for row in result] == ["b", "c", "a"]
    assert result[0]["fusion_score"] == pytest.approx(1 / 61 + 1 / 62)
    assert result[0]["vector_rank"] == 1 and result[0]["bm25_rank"] == 2
    assert result[0]["cosine_similarity"] == 0.9
    assert "vector_rank" not in result[1] and "cosine_similarity" not in result[1]
    assert result[1]["bm25_score"] == 2.5
    assert fuse([], []) == []
    assert [row["chunk_id"] for row in fuse([{"chunk_id": "b"}], [{"chunk_id": "a"}])] == ["a", "b"]
    with pytest.raises(ValueError, match="duplicate"):
        fuse([{"chunk_id": "a"}, {"chunk_id": "a"}], [])
