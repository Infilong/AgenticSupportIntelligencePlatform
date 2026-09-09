"""A failed local release upgrade must leave old writers stopped and retain its failure."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_runtime


class ReleaseFailureTests(unittest.TestCase):
    def test_failed_migration_never_initializes_checkpoints_or_restarts_writers(self):
        calls = []

        def compose(*args):
            calls.append(args)
            if 'alembic' in args:
                self.assertTrue(any(call[0] == 'stop' and 'worker' in call for call in calls))
                raise subprocess.CalledProcessError(17, ['docker', 'compose'])

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with patch.object(release_runtime, 'DIRECTORY', directory), \
                 patch.object(release_runtime, 'ENVIRONMENT', directory / 'release.env'), \
                 patch.object(release_runtime, 'compose', side_effect=compose):
                with self.assertRaises(subprocess.CalledProcessError) as error:
                    release_runtime.main('up')
        self.assertEqual(error.exception.returncode, 17)
        self.assertFalse(any('app.workflows.checkpoints' in call for call in calls))
        self.assertFalse(any(call[0] == 'up' and 'worker' in call for call in calls))
