import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "restore", Path(__file__).parents[1] / "verify_database_restore.py")
restore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore)


class RestoreTests(unittest.TestCase):
    def exercise(self, failure):
        calls = []
        original = [{"table": "alembic_version", "rows": 1, "hash": "same"}]
        snapshots = [original] * 5
        if failure == "source_changed":
            snapshots[1] = []
        if failure == "mismatch":
            snapshots[2] = []

        def run(args, **kwargs):
            calls.append(args)
            if args[0] == "pg_dump":
                kwargs["stdout"].write(b"PGDMP\x00synthetic")
            if args[0] == failure:
                raise RuntimeError("injected " + failure)
            return b"revision\n"

        with tempfile.TemporaryDirectory() as directory:
            with patch.object(restore, "ROOT", Path(directory)), \
                 patch.object(restore, "manifest", side_effect=snapshots), \
                 patch.object(restore, "run", side_effect=run), \
                 patch.object(restore, "probe_application", return_value={"status": "passed"},
                              side_effect=RuntimeError("probe failed")
                              if failure == "probe" else None):
                if failure:
                    with self.assertRaises(RuntimeError):
                        restore.main()
                else:
                    restore.main()
            report_path = next(Path(directory).glob(".artifacts/*/report.json"))
            report = json.loads(report_path.read_text())
            self.assertEqual(report["status"], "failed" if failure else "passed")
            cleanup = [args for args in calls if args[0] == "dropdb"]
            created = failure not in {"createdb", "source_changed", "pg_dump"}
            self.assertEqual(len(cleanup), int(created))
            if created:
                self.assertEqual(cleanup[0][-1], report["target"])
                self.assertNotEqual(cleanup[0][-1], restore.SOURCE)
                self.assertTrue(cleanup[0][-1].startswith("asi_restore_"))

    def test_success_and_failure_cleanup(self):
        for failure in (None, "pg_dump", "createdb", "pg_restore", "source_changed", "mismatch", "probe"):
            with self.subTest(failure=failure):
                self.exercise(failure)

    def test_cleanup_failure_is_not_reported_as_success(self):
        self.exercise("dropdb")
