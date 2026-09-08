import importlib.util
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import URLError

spec = importlib.util.spec_from_file_location("wait_http", Path(__file__).parents[1] / "wait_http.py")
wait_http = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wait_http)


class ReadinessTests(unittest.TestCase):
    def response(self, status):
        response = MagicMock()
        response.__enter__.return_value.status = status
        return response

    def test_retries_startup_errors_until_all_endpoints_are_ready(self):
        attempts = {}

        def connect(url, timeout):
            attempts[url] = attempts.get(url, 0) + 1
            self.assertGreater(timeout, 0)
            if attempts[url] == 1:
                raise URLError("not listening yet")
            return self.response(200)

        with patch.object(wait_http, "urlopen", side_effect=connect):
            self.assertTrue(wait_http.wait_ready(["http://api", "http://ui"], interval=0.001))
        self.assertEqual(attempts, {"http://api": 2, "http://ui": 2})

    def test_permanent_failure_expires_instead_of_passing(self):
        with patch.object(wait_http, "urlopen", side_effect=URLError("unavailable")):
            self.assertFalse(wait_http.wait_ready(["http://api"], timeout=0.01, interval=0.001))

    def test_non_200_does_not_count_as_ready(self):
        with patch.object(wait_http, "urlopen", return_value=self.response(503)):
            self.assertFalse(wait_http.wait_ready(["http://api"], timeout=0.01, interval=0.001))

    def test_invalid_configuration_is_rejected(self):
        for urls, timeout in [([], 1), (["file:///private"], 1), (["http://api"], 0)]:
            with self.subTest(urls=urls, timeout=timeout), self.assertRaises(ValueError):
                wait_http.wait_ready(urls, timeout)


if __name__ == "__main__":
    unittest.main()
