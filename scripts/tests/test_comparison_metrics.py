import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals"))
from comparison_metrics import discovery, paired, trace_valid
from retrieval_scoring import score_case


def row(**changes):
    return {"chunk_id": "one", "version_id": "active", "section": "POLICY",
            "vector_rank": 1, "cosine_similarity": .8, "bm25_rank": None,
            "fusion_rank": None, "selected_for_reranker": False, "reranker_score": None,
            "final_rank": 1, "exclusion": None, **changes}


class ComparisonMetricsTest(unittest.TestCase):
    def test_union_discovery_cannot_repair_selected_or_final_evidence(self):
        case = {"id": "case", "groups": [["POLICY"]]}
        trace = {"candidates": [row(fusion_rank=21, exclusion="fusion_cutoff")]}
        result = discovery(case, trace, {"active": {"state": "active"}})
        self.assertEqual(result["union40"]["groups_found"], 1)
        self.assertEqual(result["selected20"]["groups_found"], 0)
        final = score_case(case, {"results": []}, {"case": [["required fact"]]}, {})
        self.assertFalse(final["retrieval_passed"])
        foreign = discovery(case, trace, {"active": {"state": "foreign"}})
        self.assertEqual(foreign["union40"]["groups_found"], 0)

    def test_trace_rejects_wrong_strategy_duplicate_or_invented_scoring(self):
        trace = {"status": "succeeded", "phase": "completed", "trace_version": "candidate-trace-v1",
                 "strategy": "vector-v1", "candidates": [row()]}
        self.assertTrue(trace_valid(trace, "vector"))
        self.assertFalse(trace_valid(trace, "bm25"))
        self.assertFalse(trace_valid({**trace, "candidates": [row(), row()]}, "vector"))
        self.assertFalse(trace_valid({**trace, "candidates": [row(bm25_rank=1)]}, "vector"))
        self.assertFalse(trace_valid({**trace, "candidates": [row(reranker_score=.9)]}, "vector"))
        self.assertFalse(trace_valid({**trace, "phase": "started"}, "vector"))

    def test_paired_regressions_ignore_non_evidence_cases(self):
        base = [{"id": "win", "groups": [["P"]], "retrieval_passed": False},
                {"id": "loss", "groups": [["P"]], "retrieval_passed": True},
                {"id": "route", "groups": [], "retrieval_passed": None}]
        new = [{**item, "retrieval_passed": not item["retrieval_passed"]} for item in base]
        self.assertEqual(paired(new, base), {"newly_passing": ["win"], "newly_failing": ["loss"]})

    def test_required_branch_and_fusion_ranks_cannot_be_missing(self):
        common = {"status": "succeeded", "phase": "completed", "trace_version": "candidate-trace-v1"}
        self.assertFalse(trace_valid({**common, "strategy": "hybrid-v1", "candidates": [row()]}, "hybrid"))
        self.assertFalse(trace_valid({**common, "strategy": "bm25-v1", "candidates": [row(cosine_similarity=None)]}, "bm25"))

    def test_branch_ranks_must_be_contiguous_without_duplicates(self):
        common = {"status": "succeeded", "phase": "completed", "trace_version": "candidate-trace-v1", "strategy": "vector-v1"}
        self.assertFalse(trace_valid({**common, "candidates": [row(vector_rank=21)]}, "vector"))
        self.assertFalse(trace_valid({**common, "candidates": [row(), row(chunk_id="two", final_rank=2)]}, "vector"))
