"""Candidate discovery is not final passage sufficiency or semantic answer quality."""

import math

from retrieval_scoring import aggregate, safety_passed

STRATEGIES = ("vector", "bm25", "hybrid", "vector_rerank", "hybrid_rerank")
TRACE_VALIDATOR_VERSION = "candidate-ranks-v2"


def branch_ranks_valid(rows, strategy):
    hybrid = strategy.startswith("hybrid")
    branches = (
        ("vector_rank", "cosine_similarity", strategy != "bm25", not hybrid),
        ("bm25_rank", "bm25_score", strategy == "bm25" or hybrid, not hybrid),
        ("fusion_rank", "fusion_score", hybrid, True),
        ("reranker_rank", "reranker_score", strategy.endswith("rerank"), False),
    )
    for rank_key, score_key, enabled, required in branches:
        ranks = []
        for row in rows:
            rank, score = row.get(rank_key), row.get(score_key)
            if not enabled:
                if rank is not None or score is not None:
                    return False
                continue
            if (rank is None) != (score is None) or (required and rank is None):
                return False
            if rank is not None:
                if not isinstance(score, (float, int)) or not math.isfinite(score):
                    return False
                ranks.append(rank)
        if sorted(ranks) != list(range(1, len(ranks) + 1)):
            return False
    return not hybrid or all(
        row["vector_rank"] is not None or row["bm25_rank"] is not None for row in rows
    )


def discovery(case, trace, versions):
    rows = trace["candidates"]
    branches = {
        "vector20": [row for row in rows if row["vector_rank"] is not None],
        "bm25_20": [row for row in rows if row["bm25_rank"] is not None],
        "union40": rows,
        "selected20": [
            row
            for row in rows
            if row["fusion_rank"] is None or row["fusion_rank"] <= 20
        ],
    }
    result = {}
    for name, selected in branches.items():
        sections = {
            row["section"]
            for row in selected
            if versions.get(row["version_id"], {}).get("state") == "active"
        }
        result[name] = {
            "depth": len(selected),
            "groups_found": sum(
                bool(set(group) & sections) for group in case["groups"]
            ),
            "total_groups": len(case["groups"]),
        }
    return result


def trace_valid(trace, strategy):
    rows = trace["candidates"]
    ranks = [row["final_rank"] for row in rows if row["final_rank"] is not None]
    return (
        trace["status"] == "succeeded"
        and trace["phase"] == "completed"
        and branch_ranks_valid(rows, strategy)
        and trace["trace_version"] == "candidate-trace-v1"
        and trace["strategy"]
        == (
            "cosine20-mmarco-rerank-v2"
            if strategy == "vector_rerank"
            else strategy + "-v1"
        )
        and len(rows) <= (40 if strategy.startswith("hybrid") else 20)
        and len({row["chunk_id"] for row in rows}) == len(rows)
        and sum(row["vector_rank"] is not None for row in rows) <= 20
        and sum(row["bm25_rank"] is not None for row in rows) <= 20
        and sum(row["selected_for_reranker"] for row in rows) <= 20
        and sorted(ranks) == list(range(1, len(ranks) + 1))
        and len(ranks) <= 5
        and all(
            (row["reranker_score"] is not None) == row["selected_for_reranker"]
            for row in rows
        )
        and (
            strategy != "bm25" or all(row["cosine_similarity"] is None for row in rows)
        )
        and (
            strategy.endswith("rerank")
            or not any(row["selected_for_reranker"] for row in rows)
        )
        and all(
            (strategy.startswith("hybrid") or row["fusion_rank"] is None)
            and (
                strategy in {"bm25", "hybrid", "hybrid_rerank"}
                or row["bm25_rank"] is None
            )
            for row in rows
        )
    )


def summarize(cases, probes, denied):
    scores = aggregate(cases)
    times = sorted(case["elapsed_seconds"] for case in cases)
    quality = all(
        scores["all"][metric] >= 0.9
        and all(scores[lang][metric] >= 0.8 for lang in ("en", "ja", "zh"))
        for metric in ("case_success_at_5", "section_recall_at_5")
    )
    safety = (
        safety_passed(cases, probes)
        and denied == 404
        and all(
            row["trace_valid"] and not row["candidate_leakage"]
            for row in [*cases, *probes]
        )
    )
    p95 = times[math.ceil(0.95 * len(times)) - 1]
    return {
        "scores": scores,
        "quality_passed": quality,
        "safety_passed": safety,
        "warm_p95_seconds": p95,
        "latency_passed": p95 <= 3,
        "measured_requests": len(cases),
        "retrieval_gate_passed": quality and safety and p95 <= 3,
    }


def paired(cases, baseline):
    previous = {row["id"]: row for row in baseline if row["groups"]}
    return {
        "newly_passing": [
            row["id"]
            for row in cases
            if row["groups"]
            and row["retrieval_passed"]
            and not previous[row["id"]]["retrieval_passed"]
        ],
        "newly_failing": [
            row["id"]
            for row in cases
            if row["groups"]
            and not row["retrieval_passed"]
            and previous[row["id"]]["retrieval_passed"]
        ],
    }
