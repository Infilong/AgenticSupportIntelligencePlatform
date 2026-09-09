"""Old writers must be gone before schema/data changes, including standalone migration."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime


class RuntimeMigrationTests(unittest.TestCase):
    def simulate(self, command, failure=None):
        state = {"built": False, "writers": True, "migrated": False, "checkpoints": False, "started": False}

        def compose(*args):
            if args[0] == "build":
                stage = "build"
            elif args[0] == "stop":
                stage = "stop"
                self.assertTrue(state["built"])
                self.assertIn("api", args)
                self.assertIn("worker", args)
                self.assertIn("--timeout", args)
            elif args[0] == "run":
                stage = "migration" if "alembic" in args else "checkpoints"
                self.assertTrue(state["built"])
                self.assertFalse(state["writers"], "Migration raced a live legacy writer")
                self.assertIn("--no-deps", args)
            elif "worker" in args:
                stage = "start"
                self.assertTrue(state["migrated"] and state["checkpoints"])
            else:
                return 0  # Database readiness does not change application writers.
            if stage == failure:
                return 17
            if stage == "build":
                state["built"] = True
            elif stage == "stop":
                state["writers"] = False  # Synchronous completed stop, not a queued signal.
            elif stage == "migration":
                state["migrated"] = True
            elif stage == "checkpoints":
                state["checkpoints"] = True
            else:
                state["writers"] = state["started"] = True
            return 0

        with patch.object(runtime, "compose", side_effect=compose):
            code = runtime.execute(command)
        return code, state

    def test_successful_up_quiesces_before_migration_and_restarts_current_images(self):
        code, state = self.simulate("up")
        self.assertEqual(code, 0)
        self.assertTrue(state["started"])

    def test_failures_preserve_code_and_never_restart_after_a_partial_upgrade(self):
        for stage in ("build", "stop", "migration", "checkpoints"):
            with self.subTest(stage=stage):
                code, state = self.simulate("up", stage)
                self.assertEqual(code, 17)
                self.assertFalse(state["started"])
                self.assertEqual(state["writers"], stage in {"build", "stop"})
                if stage in {"build", "stop", "migration"}:
                    self.assertFalse(state["migrated"])

    def test_standalone_migration_has_no_live_writer_bypass(self):
        code, state = self.simulate("migrate")
        self.assertEqual(code, 0)
        self.assertTrue(state["migrated"])
        self.assertFalse(state["writers"] or state["started"])
