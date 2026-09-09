"""Equal-weight reciprocal rank fusion; raw branch scores remain separate."""

RRF_K = 60


def fuse(vector, lexical):
    if len(vector) > 20 or len(lexical) > 20:
        raise ValueError("Fusion accepts at most 20 candidates per branch")
    union = {}
    for name, rows in (("vector", vector), ("bm25", lexical)):
        seen = set()
        for rank, row in enumerate(rows, 1):
            key = row["chunk_id"]
            if key in seen:
                raise ValueError("A retrieval branch contains duplicate chunk identities")
            seen.add(key)
            item = union.setdefault(key, {"chunk_id": key, "fusion_score": 0.0})
            item.update(row)
            item[name + "_rank"] = rank
            item["fusion_score"] += 1 / (RRF_K + rank)
    ordered = sorted(union.values(), key=lambda row: (-row["fusion_score"], row["chunk_id"]))
    return [{**row, "fusion_rank": rank} for rank, row in enumerate(ordered, 1)]
