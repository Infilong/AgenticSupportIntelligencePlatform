"""Small local command evidence wrapper; no environment variables or secrets are recorded."""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__:
    from .command_process import capture
else:
    from command_process import capture

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / ".artifacts" / "m0"


def source_state():
    git = ["git", "-c", f"safe.directory={ROOT.as_posix()}"]
    def read(*args):
        return subprocess.check_output([*git, *args], cwd=ROOT, stderr=subprocess.PIPE)
    head = read("rev-parse", "HEAD").decode().strip()
    branch = read("branch", "--show-current").decode().strip()
    names = read("ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().split("\0")
    hashes = {}
    for name in sorted(set(names) - {""}):
        path = ROOT / name
        if not path.resolve().is_relative_to(ROOT) or path.is_symlink():
            raise ValueError("Evidence source paths must remain inside the repository")
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "deleted"
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    return {"commit": head, "branch": branch, "source_sha256": digest,
            "dirty": bool(read("status", "--porcelain").strip()), "file_sha256": hashes}


def run_checked(name, command, cwd, env=None, timeout=180):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = ARTIFACTS / f"{name}-{stamp}"
    directory.mkdir(parents=True)
    before = source_state()
    started = datetime.now(timezone.utc)
    environment = {**os.environ, **(env or {}), "ASI_EVIDENCE_DIR": str(directory)}
    try:
        result = capture(command, cwd, environment, timeout)
    except OSError:
        result = subprocess.CompletedProcess(command, 127, b"", b"Command could not be launched.\n")
    output = result.stdout + result.stderr
    (directory / "command.log").write_bytes(output)
    # Preserve raw output; Windows' default GBK decoder cannot read Playwright's UTF-8 output.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    print(output.decode("utf-8", errors="replace"), end="")
    after = source_state()
    report = {"name": name, "scope": "Named command only; not full application acceptance", "command": command,
              "exit_code": result.returncode, "source": before,
              "source_unchanged": before["source_sha256"] == after["source_sha256"],
              "elapsed_seconds": (datetime.now(timezone.utc) - started).total_seconds()}
    (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Evidence: {directory}")
    return result.returncode or int(not report["source_unchanged"])


def summarize():
    current = source_state()
    reports = {}
    for kind in ("prep", "browser"):
        candidates = sorted(ARTIFACTS.glob(f"{kind}-*/report.json"))
        if not candidates:
            reports[kind] = {"status": "NOT_VERIFIED"}
            continue
        path = candidates[-1]
        report = json.loads(path.read_text(encoding="utf-8"))
        valid = report["source"]["source_sha256"] == current["source_sha256"]
        reports[kind] = {"status": "STALE" if not valid else "PASS" if
                         report["exit_code"] == 0 and report["source_unchanged"] else "FAIL",
                         "report": str(path.relative_to(ROOT))}
    doctors = sorted(ARTIFACTS.glob("doctor-*.json"))
    if doctors:
        doctor = json.loads(doctors[-1].read_text(encoding="utf-8"))
        reports["doctor"] = {"status": doctor["status"], "report": str(doctors[-1].relative_to(ROOT)),
                             "caveat": "Environment observation; tools/ports/access may change"}
    else:
        reports["doctor"] = {"status": "NOT_VERIFIED"}
    summary = {"source": current, "checks": reports, "application": "NOT_IMPLEMENTED",
               "live_provider": "NOT_VERIFIED", "api_spend_usd": 0}
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    path = ARTIFACTS / "summary.json"
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"commit": current["commit"], "checks": reports, "evidence": str(path)}, indent=2))
    return int(any(value["status"] != "PASS" for value in reports.values()))
