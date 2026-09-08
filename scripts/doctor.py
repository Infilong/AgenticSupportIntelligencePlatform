"""Read-only preparation checks. Never prints credentials or starts services."""
import argparse
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTS = (5180, 8010, 5440)


def command_check(name, arguments, minimum=None):
    executable = shutil.which(arguments[0])
    if not executable:
        return {"name": name, "status": "FAIL", "detail": "Executable unavailable"}
    try:
        result = subprocess.run([executable, *arguments[1:]], cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return {"name": name, "status": "FAIL", "detail": "Command could not complete"}
    # Only known version commands run here; arbitrary environment/configuration is not emitted.
    output = result.stdout.strip().splitlines()
    version = output[0][:160] if output else "No version response"
    valid = result.returncode == 0
    if minimum:
        match = re.search(r"(\d+)\.(\d+)", version)
        valid = valid and bool(match) and tuple(map(int, match.groups())) >= minimum
    return {"name": name, "status": "PASS" if valid else "FAIL", "detail": version}


def port_check(port):
    try:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", port))
        return {"name": f"port_{port}", "status": "PASS", "detail": "Available now"}
    except OSError:
        return {"name": f"port_{port}", "status": "FAIL", "detail": "Unavailable; do not stop unknown owners"}


def network_check(name, url):
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            response.read(128)
        return {"name": name, "status": "PASS", "detail": "Registry metadata reachable"}
    except (OSError, ValueError):
        return {"name": name, "status": "FAIL", "detail": "Registry unavailable in this execution context"}


def collect(offline=False):
    npm = "npm.cmd" if os.name == "nt" else "npm"
    checks = [command_check("python", [sys.executable, "--version"], (3, 12)),
              command_check("git", ["git", "--version"]),
              command_check("uv", ["uv", "--version"]),
              command_check("node", ["node", "--version"], (22, 0)),
              command_check("npm", [npm, "--version"]),
              command_check("docker_compose", ["docker", "compose", "version"]),
              command_check("docker_daemon", ["docker", "info", "--format", "{{.ServerVersion}}"])]
    checks.extend(port_check(port) for port in PORTS)
    if not offline:
        checks.extend([network_check("npm_registry", "https://registry.npmjs.org/@playwright%2ftest/latest"),
                       network_check("pypi_registry", "https://pypi.org/pypi/fastapi/json")])
    else:
        checks.append({"name": "registries", "status": "NOT_VERIFIED", "detail": "Offline flag selected"})
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "scope": "M0 environment only",
            "platform": platform.platform(), "project": "asi-rebuild-v1", "checks": checks,
            "status": "FAIL" if any(c["status"] == "FAIL" for c in checks) else
                      "PARTIAL" if offline else "PASS",
            "live_provider": "NOT_VERIFIED; budget remains zero; no model calls made",
            "application": "NOT_IMPLEMENTED", "browser": "Run manage.py verify-browser separately"}


def main(arguments=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(arguments)
    report = collect(args.offline)
    directory = ROOT / ".artifacts" / "m0"
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = directory / f"doctor-{stamp}.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for check in report["checks"]:
        print(f"{check['status']:12} {check['name']}: {check['detail']}")
    print(f"Evidence: {path}")
    return int(report["status"] == "FAIL")


if __name__ == "__main__":
    raise SystemExit(main())
