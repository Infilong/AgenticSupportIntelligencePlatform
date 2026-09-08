"""Actual API ingestion and CPU retrieval evaluation against frozen, evaluator-only cases."""

import hashlib
import json
import math
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import httpx
from freeze_retrieval import CASES, FACTS, LOCK, MANIFEST, ROOT, snapshot
from retrieval_scoring import aggregate, score_case
from runtime_fingerprint import verify_runtime

sys.path.insert(0, str(ROOT.parent))
from scripts.evidence import source_state


def authenticated(credentials, role):
    client = httpx.Client(base_url="http://127.0.0.1:8010", timeout=120)
    csrf = client.get("/api/session").json()["csrf_token"]
    headers = {"Origin": "http://127.0.0.1:5180", "X-CSRF-Token": csrf}
    response = client.post(
        "/api/session/login",
        headers=headers,
        json={
            "email": credentials["accounts"][role],
            "password": credentials["password"],
        },
    )
    response.raise_for_status()
    client.headers.update({**headers, "X-CSRF-Token": response.json()["csrf_token"]})
    return client


def ingest(client, workspace, spec, previous):
    source = (ROOT / spec["path"]).read_bytes()
    response = client.post(
        f"/api/workspaces/{workspace}/documents",
        headers={"Idempotency-Key": uuid.uuid4().hex},
        files={"file": (Path(spec["path"]).name, source)},
        data={"document_id": previous} if previous else {},
    )
    response.raise_for_status()
    uploaded = response.json()
    path = f"/api/workspaces/{workspace}/documents/{uploaded['document_id']}"
    for _ in range(180):
        response = client.get(path)
        response.raise_for_status()
        state = response.json()["document"]
        if state["job_status"] == "succeeded":
            if spec["state"] == "withdrawn":
                client.patch(path, json={"withdrawn": True}).raise_for_status()
            return uploaded
        if state["job_status"] in {"failed", "cancelled"}:
            raise RuntimeError(
                f"Indexing {spec['id']} ended as {state['job_status']}: {state['error_code']}"
            )
        time.sleep(1)
    raise TimeoutError("Indexing did not finish: " + spec["id"])


def main():
    frozen = snapshot()
    if frozen != json.loads(LOCK.read_text(encoding="utf-8")):
        raise ValueError("Frozen evaluation inputs changed")
    artifact = (
        ROOT.parent
        / ".artifacts/m2"
        / ("retrieval-eval-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    )
    artifact.mkdir(parents=True)
    report = {
        "frozen": frozen,
        "status": "started",
        "documents": [],
        "cases": [],
        "source_state": source_state(),
    }
    report["revision"] = subprocess.check_output(
        ["git", "-c", "safe.directory=" + ROOT.parent.as_posix(), "rev-parse", "HEAD"],
        cwd=ROOT.parent,
        text=True,
    ).strip()

    def save():
        (artifact / "report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    save()
    clients = []
    try:
        report["runtime"] = verify_runtime()
        workspaces = json.loads(
            subprocess.check_output(
                [
                    "docker",
                    "exec",
                    "asi-rebuild-v1-api-1",
                    "/app/.venv/bin/python",
                    "-m",
                    "app.eval_workspace",
                ],
                timeout=60,
                text=True,
            )
        )
        report["workspaces"] = workspaces
        credentials = json.loads(
            (ROOT.parent / ".artifacts/m1/demo-credentials.json").read_text(
                encoding="utf-8"
            )
        )
        primary, foreign = (
            authenticated(credentials, "admin"),
            authenticated(credentials, "private"),
        )
        clients = [primary, foreign]
        families, versions = {}, {}
        for spec in json.loads(MANIFEST.read_text(encoding="utf-8"))["documents"]:
            scope = "foreign" if spec["state"] == "foreign" else "primary"
            started = time.monotonic()
            uploaded = ingest(
                foreign if scope == "foreign" else primary,
                workspaces[scope],
                spec,
                families.get(spec["family"]),
            )
            families[spec["family"]] = uploaded["document_id"]
            versions[uploaded["version_id"]] = spec
            report["documents"].append(
                {
                    "id": spec["id"],
                    **uploaded,
                    "ingestion_seconds": round(time.monotonic() - started, 3),
                }
            )
            save()
            print("Indexed " + spec["id"], flush=True)
        cases = json.loads(CASES.read_text(encoding="utf-8"))
        facts = json.loads(FACTS.read_text(encoding="utf-8"))
        endpoint = f"/api/workspaces/{workspaces['primary']}/retrieval"
        primary.post(
            endpoint, json={"query": cases[0]["question"], "limit": 5}
        ).raise_for_status()
        for case in cases:
            started = time.monotonic()
            response = primary.post(
                endpoint, json={"query": case["question"], "limit": 5}
            )
            response.raise_for_status()
            data = response.json()
            elapsed = time.monotonic() - started
            scored = score_case(case, data, facts, versions)
            report["cases"].append(
                {
                    **case,
                    **scored,
                    "elapsed_seconds": elapsed,
                    "response": data,
                    "workflow_outcome": "not_verified",
                }
            )
            save()
            print(
                f"{case['id']}: retrieval={scored['retrieval_passed']}, leakage={len(scored['leakage'])}",
                flush=True,
            )
        probes = []
        for query in (
            "Fifteen-minute lunar research travel approval response and five-day refund window",
            "Private partner refund deadline 365 days and export download 99 days",
        ):
            response = primary.post(endpoint, json={"query": query, "limit": 5})
            response.raise_for_status()
            probe = score_case(
                {"id": "probe", "groups": []}, response.json(), {}, versions
            )
            probes.append({"query": query, **probe, "response": response.json()})
        denied = primary.post(
            f"/api/workspaces/{workspaces['foreign']}/retrieval",
            json={"query": "refund deadline", "limit": 5},
        ).status_code
        report.update({"negative_probes": probes, "foreign_request_status": denied})
        scores = aggregate(report["cases"])
        times = sorted(case["elapsed_seconds"] for case in report["cases"])
        p95 = times[math.ceil(0.95 * len(times)) - 1]
        report.update(
            {
                "scores": scores,
                "warm_p95_seconds": p95,
                "status": "completed",
                "input_fingerprint": hashlib.sha256(LOCK.read_bytes()).hexdigest(),
            }
        )
        report["passed"] = (
            all(
                scores["all"][metric] >= 0.9
                and all(scores[lang][metric] >= 0.8 for lang in ("en", "ja", "zh"))
                for metric in ("case_success_at_5", "section_recall_at_5")
            )
            and not any(case["leakage"] for case in report["cases"])
            and not any(case["result_bound_violated"] for case in report["cases"])
            and not any(probe["leakage"] for probe in probes)
            and denied == 404
            and p95 <= 3
        )
        report["source_state_after"] = source_state()
        report["runtime_after"] = verify_runtime()
        report["passed"] = (
            report["passed"] and report["runtime"] == report["runtime_after"]
        )
        report["source_changed"] = (
            report["source_state"]["source_sha256"]
            != report["source_state_after"]["source_sha256"]
        )
        report["passed"] = report["passed"] and not report["source_changed"]
        save()
        print(
            json.dumps(
                {
                    "artifact": str(artifact),
                    "scores": scores,
                    "warm_p95_seconds": p95,
                    "retrieval_gate_passed": report["passed"],
                    "generation": "not_verified",
                }
            )
        )
        return 0 if report["passed"] else 1
    except Exception as error:
        report.update({"status": "failed", "error_class": type(error).__name__})
        save()
        raise
    finally:
        for client in clients:
            try:
                client.post("/api/session/logout")
            finally:
                client.close()


if __name__ == "__main__":
    raise SystemExit(main())
