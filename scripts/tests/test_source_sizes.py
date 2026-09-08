import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

CHECKER = Path(__file__).resolve().parents[1] / "check_source_sizes.py"
spec = importlib.util.spec_from_file_location("check_source_sizes", CHECKER)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class SourceSizeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in (*checker.SOURCE_ROOTS, "scripts"):
            (self.root / directory).mkdir(parents=True)
        self.baseline_path = self.root / checker.BASELINE
        self.baseline_path.write_text("{}", encoding="utf-8")

    def source(self, path, lines, newline="\n", final_newline=True):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        content = newline.join(["x"] * lines) + (newline if final_newline and lines else "")
        destination.write_bytes(content.encode("utf-8"))

    def run_check(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            status = checker.main(["--root", str(self.root)])
        return status, output.getvalue()

    def test_boundary_and_empty_files_pass(self):
        self.source("backend/app/empty.py", 0)
        self.source("frontend/src/page.tsx", 300)
        self.assertEqual(self.run_check()[0], 0)

    def test_new_oversized_file_fails_with_remediation(self):
        self.source("frontend/src/page.tsx", 301)
        status, output = self.run_check()
        self.assertEqual(status, 1)
        self.assertIn("frontend/src/page.tsx: 301 lines exceeds 300", output)
        self.assertIn("split by responsibility", output)

    def test_legacy_file_can_stay_but_cannot_grow(self):
        name = "backend/app/legacy.py"
        self.baseline_path.write_text(json.dumps({name: 420}), encoding="utf-8")
        self.source(name, 420)
        self.assertEqual(self.run_check()[0], 0)
        self.source(name, 421)
        self.assertEqual(self.run_check()[0], 1)

    def test_shrink_requires_lower_baseline(self):
        errors = checker.violations({"legacy.py": 350}, {"legacy.py": 420})
        self.assertIn("lower baseline from 420 to 350", errors[0])
        self.assertEqual(checker.violations({"legacy.py": 350}, {"legacy.py": 350}), [])

    def test_resolved_and_deleted_exceptions_must_be_removed(self):
        for sizes in ({"legacy.py": 300}, {}):
            with self.subTest(sizes=sizes):
                self.assertIn("remove", checker.violations(sizes, {"legacy.py": 420})[0])

    def test_physical_lines_are_platform_independent(self):
        for newline in ("\n", "\r\n"):
            for final in (True, False):
                with self.subTest(newline=newline, final=final):
                    self.source("backend/app/example.py", 301, newline, final)
                    self.assertEqual(checker.collect_sizes(self.root)["backend/app/example.py"], 301)

    def test_only_application_python_and_typescript_are_counted(self):
        for name in ("backend/app/nested/a.py", "frontend/src/a.ts", "frontend/src/a.tsx"):
            self.source(name, 1)
        for name in ("backend/tests/test_big.py", "frontend/src/styles.css", "frontend/dist/a.ts"):
            self.source(name, 400)
        self.assertEqual(len(checker.collect_sizes(self.root)), 3)
        self.assertEqual(self.run_check()[0], 0)

    def test_missing_source_root_is_an_error(self):
        (self.root / "frontend/src").rmdir()
        self.assertEqual(self.run_check()[0], 2)

    def test_invalid_or_missing_baseline_is_an_error(self):
        for value in ("{", "[]", '{"a.py": true}', '{"a.py": 300}', '{"a.py": "400"}'):
            with self.subTest(value=value):
                self.baseline_path.write_text(value, encoding="utf-8")
                self.assertEqual(self.run_check()[0], 2)
        self.baseline_path.unlink()
        self.assertEqual(self.run_check()[0], 2)


if __name__ == "__main__":
    unittest.main()
