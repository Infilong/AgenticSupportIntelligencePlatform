import copy
import json
import re
import socket
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_fixtures import load, validate
from doctor import command_check, port_check
import evidence


class PreparationTests(unittest.TestCase):
    def test_committed_fixture_contract(self):
        manifest, cases, directory = load()
        self.assertEqual(validate(manifest, cases, directory), [])
        self.assertEqual(Counter(case["language"] for case in cases), {"en": 5, "ja": 5, "zh": 5})
        self.assertTrue(manifest["synthetic"])
        for language in ("ja", "zh"):
            self.assertTrue(any(case["language"] == language and any(
                source["id"] == "incidents-en" for source in case["sources"]) for case in cases))

    def test_missing_and_historical_sources_fail(self):
        manifest, cases, directory = load()
        broken = copy.deepcopy(cases)
        broken[0]["sources"][0]["version"] = 1
        self.assertTrue(validate(manifest, broken, directory))
        broken[0]["sources"][0]["version"] = 999
        self.assertTrue(validate(manifest, broken, directory))

    def test_missing_sections_and_duplicate_identity_fail(self):
        manifest, cases, directory = load()
        broken = copy.deepcopy(cases)
        broken[0]["sources"][0]["section"] = "NONEXISTENT"
        broken.append(copy.deepcopy(broken[0]))
        errors = validate(manifest, broken, directory)
        self.assertTrue(any("Missing section" in error for error in errors))
        self.assertTrue(any("Duplicate case" in error for error in errors))

    def test_multiple_active_versions_fail(self):
        manifest, cases, directory = load()
        manifest["documents"][0]["active"] = True
        self.assertIn("Multiple active versions of one document", validate(manifest, cases, directory))

    def test_missing_tool_is_a_failure(self):
        with patch("doctor.shutil.which", return_value=None):
            self.assertEqual(command_check("tool", ["missing"])["status"], "FAIL")

    def test_occupied_port_is_a_failure(self):
        with socket.socket() as occupied:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen()
            self.assertEqual(port_check(occupied.getsockname()[1])["status"], "FAIL")

    def test_failed_command_preserves_nonzero_evidence(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(evidence, "ARTIFACTS", Path(temp)), \
                patch.object(evidence, "source_state", return_value={"source_sha256": "fixed"}):
            code = evidence.run_checked("injected-failure", [sys.executable, "-c", "raise SystemExit(7)"], Path(temp))
            report = json.loads(next(Path(temp).glob("*/report.json")).read_text())
            self.assertEqual(code, 7)
            self.assertEqual(report["exit_code"], 7)
            self.assertTrue(report["source_unchanged"])

    def test_source_change_invalidates_success(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(evidence, "ARTIFACTS", Path(temp)), \
                patch.object(evidence, "source_state", side_effect=[{"source_sha256": "before"}, {"source_sha256": "after"}]):
            code = evidence.run_checked("source-change", [sys.executable, "-c", "pass"], Path(temp))
            self.assertEqual(code, 1)

    def test_utf8_process_output_is_preserved_as_bytes(self):
        raw = "返金 / 退款 / ✓".encode("utf-8")
        with tempfile.TemporaryDirectory() as temp, patch.object(evidence, "ARTIFACTS", Path(temp)), \
                patch.object(evidence, "source_state", return_value={"source_sha256": "fixed"}):
            command = [sys.executable, "-c", f"import sys; sys.stdout.buffer.write({raw!r})"]
            self.assertEqual(evidence.run_checked("unicode", command, Path(temp)), 0)
            self.assertEqual(next(Path(temp).glob("*/command.log")).read_bytes(), raw)

    def test_document_links_resolve(self):
        root = Path(__file__).resolve().parents[2]
        docs = [root / "README.md", root / "AGENTS.md", root / "REBUILD_PLAN.md", *root.glob("docs/**/*.md")]
        for doc in docs:
            for link in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
                if "://" not in link and not link.startswith("#"):
                    self.assertTrue((doc.parent / link.split("#")[0]).exists(), f"{doc.name}: {link}")


if __name__ == "__main__":
    unittest.main()
