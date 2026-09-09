"""Exercise actual inherited pipes; mocking subprocess misses orphaned children."""

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from command_process import capture


class CommandTreeTests(unittest.TestCase):
    def test_failed_termination_preserves_timeout_and_partial_output(self):
        process = Mock(pid=123)
        process.wait.side_effect = subprocess.TimeoutExpired(["synthetic"], 1)
        process.poll.return_value = None
        process.kill.side_effect = PermissionError("Synthetic termination denial")

        def launch(*args, **kwargs):
            kwargs["stdout"].write(b"partial evidence\n")
            return process

        with patch("command_process.subprocess.Popen", side_effect=launch), \
                patch("command_process.subprocess.run", return_value=Mock(returncode=1)), \
                patch("command_process.os.killpg", side_effect=OSError(), create=True):
            result = capture(["synthetic"], Path.cwd(), os.environ.copy(), 1)
        self.assertEqual(result.returncode, 124)
        self.assertIn(b"partial evidence", result.stdout)
        self.assertIn(b"termination could not be confirmed", result.stderr)
        self.assertIn(b"exit could not be confirmed", result.stderr)

    def test_timeout_stops_child_and_preserves_unrelated_process(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            # The sibling is deliberately outside the launched command's process tree/session.
            sibling = subprocess.Popen([
                sys.executable, "-c",
                "import time,pathlib; time.sleep(4); pathlib.Path('sibling').write_text('alive')",
            ], cwd=root)
            child = "import time,pathlib; print('child ready',flush=True); time.sleep(5); " \
                    "pathlib.Path('child-survived').write_text('leaked')"
            parent = (
                "import subprocess,sys,time; "
                f"subprocess.Popen([sys.executable,'-c',{child!r}]); time.sleep(60)"
            )
            try:
                started = time.monotonic()
                result = capture([sys.executable, "-c", parent], root, os.environ.copy(), 2)
                self.assertEqual(result.returncode, 124)
                self.assertIn(b"child ready", result.stdout)
                self.assertIn(b"timed out after 2 seconds", result.stderr)
                self.assertNotIn(b"could not be confirmed", result.stderr)
                self.assertLess(time.monotonic() - started, 8)
                sibling.wait(timeout=8)
                time.sleep(3.5)  # Past the child's write deadline: a leak must be observable.
                self.assertFalse((root / "child-survived").exists())
                self.assertEqual((root / "sibling").read_text(), "alive")
            finally:
                if sibling.poll() is None:
                    sibling.kill()
                    sibling.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
