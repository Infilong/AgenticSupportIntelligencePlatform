import unittest
import json

from evals.freeze_retrieval import LOCK, snapshot

from evals.retrieval_scoring import safety_passed, score_case


class RetrievalScoringTest(unittest.TestCase):
    def test_negative_probe_result_limit_is_a_global_gate(self):
        probe = score_case(
            {"id": "probe", "groups": []},
            {"results": [{"section": "OTHER", "text": "Other", "version_id": "ok"}] * 6},
            {}, {"ok": {"state": "active"}},
        )
        self.assertIsNone(probe["retrieval_passed"])
        self.assertFalse(safety_passed([], [probe]))
        self.assertTrue(safety_passed([], [{"leakage": [], "result_bound_violated": False}]))

    def test_frozen_inputs_remain_unchanged(self):
        self.assertEqual(snapshot(), json.loads(LOCK.read_text(encoding="utf-8")))

    def test_sixth_result_cannot_satisfy_top_five(self):
        rows = [{"section": "OTHER", "text": "Unrelated", "version_id": "ok"}] * 5
        rows.append({"section": "REFUND", "text": "14 calendar days", "version_id": "ok"})
        result = score_case({"id": "one", "groups": [["REFUND"]]}, {"results": rows},
                            {"one": [["14 calendar days"]]}, {"ok": {"state": "active"}})
        self.assertFalse(result["retrieval_passed"])
        self.assertTrue(result["result_bound_violated"])
        self.assertEqual(result["groups_found"], 0)

    def test_section_without_fact_cannot_pass(self):
        result = score_case(
            {"id": "one", "groups": [["REFUND"]]},
            {
                "results": [
                    {
                        "section": "REFUND",
                        "text": "Keep the receipt.",
                        "version_id": "ok",
                    }
                ]
            },
            {"one": [["14 calendar days"]]},
            {"ok": {"state": "active"}},
        )
        self.assertEqual(result["groups_found"], 1)
        self.assertFalse(result["retrieval_passed"])

    def test_matching_foreign_fact_is_still_failure(self):
        result = score_case(
            {"id": "one", "groups": [["REFUND"]]},
            {
                "results": [
                    {
                        "section": "REFUND",
                        "text": "14 calendar days",
                        "version_id": "foreign",
                    }
                ]
            },
            {"one": [["14 calendar days"]]},
            {"foreign": {"state": "foreign"}},
        )
        self.assertEqual(result["leakage"], ["foreign"])
        self.assertFalse(result["retrieval_passed"])
        self.assertEqual(result["fact_results"], [False])

    def test_unrelated_section_cannot_supply_required_fact(self):
        result = score_case(
            {"id": "one", "groups": [["REFUND"]]},
            {"results": [
                {"section": "REFUND", "text": "Keep the receipt.", "version_id": "ok"},
                {"section": "TRAVEL", "text": "14 calendar days", "version_id": "ok"},
            ]},
            {"one": [["14 calendar days"]]},
            {"ok": {"state": "active"}},
        )
        self.assertEqual(result["groups_found"], 1)
        self.assertEqual(result["fact_results"], [False])
        self.assertFalse(result["retrieval_passed"])

    def test_supported_translated_alternative_can_pass(self):
        result = score_case(
            {"id": "one", "groups": [["REFUND"]]},
            {
                "results": [
                    {"section": "REFUND", "text": "14暦日以内", "version_id": "ja"}
                ]
            },
            {"one": [["14 calendar days", "14暦日以内"]]},
            {"ja": {"state": "active"}},
        )
        self.assertTrue(result["retrieval_passed"])
