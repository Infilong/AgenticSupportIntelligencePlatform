import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.verify_built_web import inspect_runtime, verify


class BuiltRuntimeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.config = {"uid": 10001, "node": None, "npm": None, "environment": "production"}
        self.logs = json.dumps({"event": "http_request", "status": 200, "error_type": None})

    def test_accepts_nonroot_production_runtime_with_outcomes(self):
        self.assertEqual(inspect_runtime(self.config, self.logs)["http_outcomes"], 1)

    def test_rejects_development_root_or_node_runtime(self):
        for changes in ({"uid": 0}, {"environment": "local"}, {"node": "/bin/node"},
                        {"npm": "/bin/npm"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                inspect_runtime({**self.config, **changes}, self.logs)

    def test_rejects_missing_or_failed_http_evidence(self):
        for logs in ("startup only", '{"event":"http_request","status":500}',
                     '{"event":"http_request","status":200,"error_type":"RuntimeError"}'):
            with self.subTest(logs=logs), self.assertRaises(ValueError):
                inspect_runtime(self.config, logs)

    def test_browser_failure_still_cleans_only_generated_containers(self):
        commands = []

        def execute(command, **kwargs):
            commands.append(command)
            return type("Result", (), {"returncode": 1 if "playwright" in command else 0})()

        with TemporaryDirectory() as directory:
            with patch("scripts.verify_built_web.ROOT", Path(directory)), \
                    patch("scripts.verify_built_web.subprocess.run", side_effect=execute):
                with self.assertRaisesRegex(RuntimeError, "browser failed"):
                    verify("asi-verification", 8001)
            removals = [command[-1] for command in commands if command[:3] == ["docker", "rm", "-f"]]
            self.assertEqual(len(removals), 3)
            self.assertTrue(any(name.endswith("-worker") for name in removals))
            self.assertTrue(any(command[-3:] == ["python", "-m", "app.worker"] for command in commands))
            self.assertTrue(all(name.startswith("asi-verification-web-") for name in removals))
            self.assertNotIn("asi-verification-api-1", removals)
