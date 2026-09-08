import json
import unittest

from scripts.check_http_log_privacy import inspect_logs


class HttpLogPrivacyTests(unittest.TestCase):
    def outcome(self):
        return json.dumps({"event": "http_request", "request_id": "reference", "status": 404,
                           "route": "<unmatched>", "error_type": None})

    def test_safe_correlated_outcome_is_required(self):
        inspect_logs("api | " + self.outcome(), "reference", "private-marker")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            inspect_logs("", "reference", "private-marker")

    def test_duplicate_access_log_cannot_hide_behind_safe_outcome(self):
        with self.assertRaisesRegex(ValueError, "Raw synthetic"):
            inspect_logs(self.outcome() + "\nGET /private-marker HTTP/1.1", "reference",
                         "private-marker")

    def test_wrong_outcomes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "route/status"):
            inspect_logs(self.outcome().replace("404", "500"), "reference", "private-marker")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            inspect_logs(self.outcome() + "\n" + self.outcome(), "reference", "private-marker")
