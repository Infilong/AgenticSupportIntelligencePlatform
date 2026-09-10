"""Capture a separately versioned local-live batch on an unchanged frozen corpus."""

import argparse
import json
from pathlib import Path

import httpx
from freeze_retrieval import CASES, LOCK, ROOT, snapshot
from generation_batch import case_rows, save
from generation_session import authenticate
from generation_scoring import digest
from local_snapshot import export
from run_retrieval import source_state
from runtime_fingerprint import verify_runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "collect"])
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--corpus-report", type=Path)
    args = parser.parse_args()
    directory = args.directory.resolve()
    if not directory.is_relative_to((ROOT.parent / ".artifacts").resolve()):
        parser.error("Evidence must stay under repository .artifacts")
    frozen, runtime = snapshot(), verify_runtime()
    if frozen != json.loads(LOCK.read_text(encoding="utf-8")):
        raise ValueError("Frozen corpus changed")
    if args.action == "prepare":
        if args.corpus_report is None:
            parser.error("prepare requires a previously ingested frozen corpus report")
        prior = json.loads(args.corpus_report.read_text(encoding="utf-8"))
        if prior["frozen"] != frozen or not prior["corpus_ready"]:
            raise ValueError("Source corpus is not the frozen, ingested corpus")
        directory.mkdir(parents=True, exist_ok=False)
        report = {
            "experiment": "local-generation-batch-v1",
            "frozen": frozen,
            "runtime": runtime,
            "source_state": source_state(),
            "workspaces": prior["workspaces"],
            "documents": prior["documents"],
            "corpus_hash": prior["corpus_hash"],
            "cases": case_rows(json.loads(CASES.read_text(encoding="utf-8"))),
            "generation_quality": "not_verified",
        }
    else:
        report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
        if (
            report["experiment"] != "local-generation-batch-v1"
            or report["frozen"] != frozen
            or report["runtime"] != runtime
        ):
            raise ValueError("Batch mode, inputs or runtime changed")
    report["status"] = "collecting"
    report.pop("evidence_hash", None)
    report.pop("runtime_after", None)
    save(report, directory)
    credentials = json.loads(
        (ROOT.parent / ".artifacts/m1/demo-credentials.json").read_text(encoding="utf-8")
    )
    with httpx.Client(base_url="http://127.0.0.1:8010", timeout=120, trust_env=False) as client:
        authenticate(client, credentials, ROOT.parent / ".artifacts/m5/local-generation-session.json")
        endpoint = f"/api/workspaces/{report['workspaces']['primary']}/comparisons"
        for row in report["cases"]:
            try:
                if not row["comparison_id"]:
                    response = client.post(
                        endpoint,
                        headers={"Idempotency-Key": row["key"]},
                        json={
                            "original": row["question"],
                            "language": row["language"],
                            "generation_mode": "local_ollama",
                        },
                    )
                    response.raise_for_status()
                    row["comparison_id"] = response.json()["id"]
                    save(report, directory)
                response = client.get(f"{endpoint}/{row['comparison_id']}")
                response.raise_for_status()
                detail = response.json()
                if not detail["comparable"] or detail["corpus_hash"] != report["corpus_hash"]:
                    raise ValueError("Corpus changed; preserve failed batch")
                if any(p["configuration"]["transport"] != "local_ollama" for p in detail["pipelines"]):
                    raise ValueError("Mixed generation transports")
                row["detail"], row["error"] = detail, None
            except Exception as error:
                row["error"] = {"type": type(error).__name__, "message": str(error)}
                row["failures"].append(row["error"])
            save(report, directory)
    evidence = export(
        report["workspaces"]["primary"], [r["comparison_id"] for r in report["cases"] if r["comparison_id"]]
    )
    (directory / "local-evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    runtime_after = verify_runtime()
    if runtime_after != runtime:
        raise ValueError("Runtime changed during collection")
    report["runtime_after"] = runtime_after
    report["evidence_hash"] = digest(evidence)
    report["status"] = (
        "collection_failed" if any(row["error"] for row in report["cases"]) else "snapshot_collected"
    )
    save(report, directory)
    print(json.dumps(report["summary"]["all"], ensure_ascii=False))
    return int(any(row["error"] for row in report["cases"]))


if __name__ == "__main__":
    raise SystemExit(main())
