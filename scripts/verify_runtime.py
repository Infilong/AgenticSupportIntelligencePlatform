"""Verify the real API/database boundary and recovery in the isolated rebuild stack."""
import json
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from evidence import source_state
from runtime import ROOT, compose

BASE_URL = "http://127.0.0.1:8010"


def request(path):
    try:
        response = urllib.request.urlopen(BASE_URL + path, timeout=10)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return {"status": response.status, "body": json.load(response),
                "request_id": response.headers.get("x-request-id")}


def main():
    directory = ROOT / ".artifacts/m1" / datetime.now(timezone.utc).strftime("runtime-%Y%m%dT%H%M%SZ")
    directory.mkdir(parents=True)
    report = {"scope": "API/database health and recovery only", "checks": {}, "source": source_state()}
    stopped = False
    try:
        # Confirm actual container ownership immediately before fault injection.
        output = subprocess.check_output([
            "docker", "inspect", "asi-rebuild-v1-postgres-1", "--format",
            '{{index .Config.Labels "com.docker.compose.project"}} {{.State.Running}}',
        ], text=True).strip()
        assert output == "asi-rebuild-v1 true", "Expected live isolated rebuild PostgreSQL"
        healthy = request("/api/health/ready")
        report["checks"]["healthy"] = healthy
        assert healthy["status"] == 200 and healthy["body"]["status"] == "ready"
        assert healthy["request_id"], "Missing correlation ID"
        assert compose("stop", "postgres") == 0, "Failed controlled database stop"
        stopped = True
        unavailable = request("/api/health/ready")
        report["checks"]["database_stopped"] = unavailable
        assert unavailable["status"] == 503
        assert request("/api/health/live")["status"] == 200
    finally:
        if stopped:
            report["restart_exit"] = compose("up", "-d", "--wait", "postgres")
        (directory / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    assert report["restart_exit"] == 0, "Could not restore the controlled database service"
    recovered = request("/api/health/ready")
    for _ in range(10):
        if recovered["status"] == 200:
            break
        time.sleep(1)
        recovered = request("/api/health/ready")
    report["checks"]["recovered"] = recovered
    assert recovered["status"] == 200, "Database recovery did not restore API readiness"
    logs = subprocess.check_output(["docker", "logs", "asi-rebuild-v1-api-1"], stderr=subprocess.STDOUT)
    (directory / "api.log").write_bytes(logs)
    assert healthy["request_id"].encode() in logs, "Request cannot be correlated to server log"
    report["source_unchanged"] = report["source"]["source_sha256"] == source_state()["source_sha256"]
    assert report["source_unchanged"], "Source changed during runtime verification; re-run against stable source"
    report["status"] = "PASS"
    (directory / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Runtime boundary and recovery passed. Evidence: {directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
