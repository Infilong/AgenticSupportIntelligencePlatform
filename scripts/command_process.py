"""Bounded command capture, including children that inherit output handles."""

import os
import signal
import subprocess
import tempfile


def capture(command, cwd, env, timeout):
    # File-backed capture avoids reader threads waiting forever on inherited output pipes.
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(
            command, cwd=cwd, env=env, stdout=output, stderr=errors,
            start_new_session=os.name != "nt",
        )
        suffix = b""
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            code = 124
            suffix = f"Command timed out after {timeout} seconds.\n".encode()
            try:
                if os.name == "nt":
                    # Kill descendants before the launcher disappears; killing uv alone leaks pytest.
                    result = subprocess.run(
                        ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                        capture_output=True, timeout=10,
                    )
                    if result.returncode:
                        suffix += b"Process-tree cleanup could not be confirmed.\n"
                else:
                    os.killpg(process.pid, signal.SIGKILL)
            except (OSError, subprocess.TimeoutExpired):
                suffix += b"Process-tree cleanup could not be confirmed.\n"
            if process.poll() is None:
                try:
                    process.kill()
                except OSError:
                    suffix += b"Launcher termination could not be confirmed.\n"
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                suffix += b"Launcher exit could not be confirmed after cleanup.\n"
        output.seek(0)
        errors.seek(0)
        return subprocess.CompletedProcess(command, code, output.read(), errors.read() + suffix)
