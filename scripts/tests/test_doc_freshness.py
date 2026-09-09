import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from doc_reference import render
from doc_sources import GENERATED, MANIFEST, RECEIPTS, files, safe_path, snapshot
from docs_freshness import acknowledge, report


class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.write(".gitignore", "ignored/\n")
        self.write("scripts/manage.py", 'parser.add_argument("command", choices=["doctor", "up"])\n')
        self.write("frontend/package.json", '{"scripts": {"build": "tsc"}}')
        self.write("backend/app/modules/demo/service.py", "value = 1\n")
        self.write("backend/policy.md", "Original policy\n")
        self.write("docs/owner.md", "Current behavior\n")
        self.config = {"version": 1, "areas": {"app": {
            "sources": ["backend/", "scripts/", "frontend/", ".gitignore"], "docs": ["docs/owner.md"]}}}
        self.write(MANIFEST, json.dumps(self.config))
        self.write(GENERATED, render(self.root))

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")

    def fingerprint(self):
        return snapshot(self.root)[0]["app"]["fingerprint"]

    def review(self):
        acknowledge(self.root, "app", self.fingerprint(), "independent-test-reviewer",
                    "no-doc-impact", "Verified owner claims against the test source.")

    def test_initial_review_and_deterministic_generation(self):
        self.assertTrue(report(self.root)["errors"])
        self.assertEqual(render(self.root), render(self.root))
        self.assertIn("python scripts/manage.py doctor", render(self.root))
        self.assertIn("backend/app/modules/demo/", render(self.root))
        self.review()
        self.assertEqual(report(self.root)["errors"], [])

    def test_reference_groups_files_by_actual_containing_directory(self):
        self.write("backend/app/main.py", "app = None\n")
        self.write("frontend/src/styles.css", "body {}\n")
        reference = render(self.root)
        self.assertIn("| `backend/app/` | 1 |", reference)
        self.assertIn("| `frontend/src/` | 1 |", reference)
        self.assertNotIn("main.py/", reference)
        self.assertNotIn("styles.css/", reference)

    def test_source_change_touch_and_document_date_cannot_clear_staleness(self):
        self.review()
        self.write("backend/app/modules/demo/service.py", "value = 2\n")
        os.utime(self.root / "docs/owner.md", None)
        self.assertTrue(report(self.root)["errors"])
        self.write("docs/owner.md", "Updated today\n")
        self.assertTrue(report(self.root)["errors"])

    def test_touch_only_and_crlf_are_not_content_changes(self):
        self.review()
        os.utime(self.root / "docs/owner.md", None)
        (self.root / "docs/owner.md").write_bytes(b"\xef\xbb\xbfCurrent behavior\r\n")
        self.assertEqual(report(self.root)["errors"], [])

    def test_new_deleted_and_renamed_sources_invalidate(self):
        self.review()
        self.write("backend/new.py", "new = True\n")
        self.assertTrue(report(self.root)["errors"])
        self.review()
        (self.root / "backend/new.py").rename(self.root / "backend/renamed.py")
        self.assertTrue(report(self.root)["errors"])
        self.review()
        (self.root / "backend/renamed.py").unlink()
        self.assertTrue(report(self.root)["errors"])

    def test_corpus_markdown_and_owning_docs_invalidate(self):
        self.review()
        self.write("backend/policy.md", "Changed policy\n")
        self.assertTrue(report(self.root)["errors"])
        self.review()
        self.write("docs/owner.md", "Changed claim\n")
        self.assertTrue(report(self.root)["errors"])

    def test_mapping_change_invalidates_and_missing_zero_match_fail(self):
        original = self.fingerprint()
        self.config["areas"]["app"]["sources"].append("future/")
        self.write(MANIFEST, json.dumps(self.config))
        self.assertNotEqual(original, self.fingerprint())
        self.config["areas"]["empty"] = {"sources": ["missing/"], "docs": ["docs/missing.md"]}
        self.write(MANIFEST, json.dumps(self.config))
        self.assertEqual(len(snapshot(self.root)[1]), 2)

    def test_unmapped_source_and_ignored_files(self):
        self.review()
        self.write("ignored/secret.txt", "must not be read")
        self.assertNotIn("ignored/secret.txt", files(self.root))
        self.assertEqual(report(self.root)["errors"], [])
        self.write("unknown/data.json", "{}")
        self.assertTrue(any("Unmapped source" in e for e in report(self.root)["errors"]))

    def test_receipt_rejects_changed_snapshot_and_empty_rationale(self):
        old = self.fingerprint()
        self.write("backend/policy.md", "Changed\n")
        with self.assertRaises(ValueError):
            acknowledge(self.root, "app", old, "reviewer", "updated", "Reviewed")
        with self.assertRaises(ValueError):
            acknowledge(self.root, "app", self.fingerprint(), "reviewer", "updated", " ")
        self.assertFalse((self.root / RECEIPTS).exists())

    def test_stale_generated_reference_is_independent_of_receipts(self):
        self.review()
        self.write(GENERATED, "incorrect reference\n")
        self.assertTrue(any("stale/missing; run" in e for e in report(self.root)["errors"]))
        self.assertTrue(report(self.root)["areas"]["app"]["current"])

    def test_unsafe_manifest_paths(self):
        for name in ("../outside", "/absolute", "C:/outside", "a\\b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                safe_path(self.root, name)
        self.config["areas"]["app"]["docs"] = ["../outside.md"]
        self.write(MANIFEST, json.dumps(self.config))
        with self.assertRaises(ValueError):
            snapshot(self.root)

    def test_unsupported_dispatcher_fails_without_execution(self):
        self.write("scripts/manage.py", 'raise RuntimeError("must not execute")\nparser.add_argument("command", choices=get_commands())')
        with self.assertRaises(ValueError):
            render(self.root)

    def test_bom_sources_and_scalar_command_choices(self):
        before, fingerprint = render(self.root), self.fingerprint()
        for name in ("scripts/manage.py", "frontend/package.json"):
            path = self.root / name
            path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
        self.assertEqual(render(self.root), before)
        self.assertEqual(self.fingerprint(), fingerprint)
        self.write("scripts/manage.py", 'parser.add_argument("command", choices="doctor")')
        with self.assertRaises(ValueError):
            render(self.root)

    def test_symlink_rejected(self):
        link = self.root / "linked"
        try:
            link.symlink_to(self.root / "backend", target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Host does not permit test symlinks: {exc}")
        with self.assertRaises(ValueError):
            safe_path(self.root, "linked/policy.md")

    def test_tracked_deletion_invalidates_without_index_update(self):
        subprocess.run(["git", "-c", f"safe.directory={self.root.as_posix()}",
                        "add", "backend/policy.md"], cwd=self.root, check=True, capture_output=True)
        self.review()
        (self.root / "backend/policy.md").unlink()
        self.assertTrue(report(self.root)["errors"])

    def test_malformed_receipt_shape_is_actionable(self):
        self.write(RECEIPTS, '["not a receipt mapping"]')
        with self.assertRaisesRegex(ValueError, "Review receipts"):
            report(self.root)


if __name__ == "__main__":
    unittest.main()
