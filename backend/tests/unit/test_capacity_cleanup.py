"""A timed-out test launcher must retain output and stop its actual child process."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from time import monotonic, sleep

import pytest

from tests.integration.capacity_browser import launch, stop


def test_timeout_cleanup_stops_child_and_preserves_streamed_output():
    child = "import time; print('child-ready', flush=True); time.sleep(60)"
    parent = (
        "import subprocess,sys,time; "
        f"p=subprocess.Popen([sys.executable,'-c',{child!r}], "
        "stdout=sys.stdout,stderr=sys.stderr,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)); "
        "print('child-pid:'+str(p.pid),flush=True); time.sleep(60)"
    )
    with tempfile.TemporaryDirectory(prefix="asi-capacity-cleanup-") as directory:
        path = Path(directory) / "launcher.log"
        with path.open("wb") as log:
            process = launch([sys.executable, "-c", parent], stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = monotonic() + 5
                while "child-ready" not in path.read_text() and monotonic() < deadline:
                    sleep(0.02)
                output = path.read_text()
                assert "child-ready" in output
                child_id = int(
                    next(line.split(":")[1] for line in output.splitlines() if line.startswith("child-pid:"))
                )
                with pytest.raises(subprocess.TimeoutExpired):
                    process.wait(timeout=0.05)
            finally:
                stop(process)
        assert "child-ready" in path.read_text()
        if os.name == "nt":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {child_id}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            assert f'"{child_id}"' not in result.stdout
        else:
            result = subprocess.run(
                ["ps", "-p", str(child_id), "-o", "stat="], capture_output=True, text=True, timeout=10
            )
            assert not result.stdout.strip() or result.stdout.strip().startswith("Z")
