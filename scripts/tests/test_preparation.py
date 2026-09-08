import copy
import json
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
from check_docs import repository_docs, validate as validate_docs


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

    def test_timed_out_command_retains_partial_output(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(evidence, "ARTIFACTS", Path(temp)), \
                patch.object(evidence, "source_state", return_value={"source_sha256": "fixed"}):
            command = [sys.executable, "-c", "import time; print('before timeout', flush=True); time.sleep(5)"]
            self.assertEqual(evidence.run_checked("timeout", command, Path(temp), timeout=1), 124)
            output = next(Path(temp).glob("*/command.log")).read_bytes()
            self.assertIn(b"before timeout", output)
            self.assertIn(b"timed out after 1 seconds", output)

    def test_utf8_process_output_is_preserved_as_bytes(self):
        raw = "返金 / 退款 / ✓".encode("utf-8")
        with tempfile.TemporaryDirectory() as temp, patch.object(evidence, "ARTIFACTS", Path(temp)), \
                patch.object(evidence, "source_state", return_value={"source_sha256": "fixed"}):
            command = [sys.executable, "-c", f"import sys; sys.stdout.buffer.write({raw!r})"]
            self.assertEqual(evidence.run_checked("unicode", command, Path(temp)), 0)
            self.assertEqual(next(Path(temp).glob("*/command.log")).read_bytes(), raw)

    def test_document_links_resolve(self):
        root = Path(__file__).resolve().parents[2]
        docs = repository_docs(root)
        self.assertIn("frontend/AGENTS.md", docs)
        self.assertIn("backend/AGENTS.md", docs)
        self.assertEqual(validate_docs(root, docs), [])

    def test_nested_broken_link_is_actionable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "frontend").mkdir()
            (root / "frontend/AGENTS.md").write_text("[guide](missing.md)", encoding="utf-8")
            errors = validate_docs(root, ["frontend/AGENTS.md"])
            self.assertEqual(len(errors), 1)
            self.assertIn("frontend/AGENTS.md", errors[0])
            self.assertIn("fix the path", errors[0])

    def test_instruction_limit_rejects_200_lines(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            guide = root / "AGENTS.md"
            guide.write_text("rule\n" * 199, encoding="utf-8")
            self.assertEqual(validate_docs(root, ["AGENTS.md"]), [])
            guide.write_text("rule\n" * 200, encoding="utf-8")
            self.assertIn("under 200 lines", validate_docs(root, ["AGENTS.md"])[0])

    def test_encoded_local_link_and_external_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a file.md").write_text("target", encoding="utf-8")
            (root / "README.md").write_text(
                '[local](a%20file.md#section) [web](https://example.test/missing)\n'
                '```text\n[example](not-a-real-file)\n```', encoding="utf-8")
            self.assertEqual(validate_docs(root, ["README.md"]), [])


if __name__ == "__main__":
    unittest.main()
