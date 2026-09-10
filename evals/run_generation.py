"""Prepare and recollect all frozen generation cases with real local retrieval."""

import argparse
import json
import subprocess
from contextlib import ExitStack
from pathlib import Path

import httpx
from freeze_retrieval import CASES, LOCK, MANIFEST, ROOT, snapshot
from generation_batch import case_rows, collect, save
from generation_session import authenticate
from run_retrieval import authenticated, ingest, source_state
from runtime_fingerprint import verify_runtime


def prepare(report, directory, primary, foreign):
    report["workspaces"] = json.loads(
        subprocess.check_output(
            ["docker", "exec", "asi-rebuild-v1-api-1", "/app/.venv/bin/python", "-m", "app.eval_workspace"],
            timeout=60,
            text=True,
        )
    )
    save(report, directory)
    families = {}
    for spec in json.loads(MANIFEST.read_text(encoding="utf-8"))["documents"]:
        scope = "foreign" if spec["state"] == "foreign" else "primary"
        uploaded = ingest(
            foreign if scope == "foreign" else primary,
            report["workspaces"][scope],
            spec,
            families.get(spec["family"]),
        )
        families[spec["family"]] = uploaded["document_id"]
        report["documents"].append({"spec": spec, **uploaded})
        save(report, directory)
        print("Indexed " + spec["id"], flush=True)
    report["corpus_ready"] = True
    save(report, directory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "collect"])
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument(
        "--credentials", type=Path, default=ROOT.parent / ".artifacts/m1/demo-credentials.json"
    )
    parser.add_argument("--session", type=Path, default=ROOT.parent / ".artifacts/m5/generation-session.json")
    args = parser.parse_args()
    directory = args.directory.resolve()
    if not directory.is_relative_to((ROOT.parent / ".artifacts").resolve()):
        parser.error("Evidence directory must stay under repository .artifacts")
    frozen = snapshot()
    if frozen != json.loads(LOCK.read_text(encoding="utf-8")):
        raise ValueError("Frozen evaluation inputs changed")
    runtime = verify_runtime()
    if args.action == "prepare":
        directory.mkdir(parents=True, exist_ok=False)
        report = {
            "experiment": "generation-batch-v1",
            "frozen": frozen,
            "runtime": runtime,
            "source_state": source_state(),
            "documents": [],
            "corpus_ready": False,
            "cases": case_rows(json.loads(CASES.read_text(encoding="utf-8"))),
            "generation_quality": "not_verified",
            "status": "preparing",
        }
        save(report, directory)
    else:
        report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
        if report["frozen"] != frozen or report["runtime"] != runtime or not report["corpus_ready"]:
            raise ValueError("Batch inputs/runtime changed or ingestion incomplete; preserve this report")
        expected = [
            {key: case[key] for key in ("id", "question", "language")}
            for case in json.loads(CASES.read_text(encoding="utf-8"))
        ]
        if [{key: row[key] for key in ("id", "question", "language")} for row in report["cases"]] != expected:
            raise ValueError("Batch cases differ from frozen cases")
    credentials = json.loads(args.credentials.read_text(encoding="utf-8"))
    try:
        with ExitStack() as stack:
            primary = stack.enter_context(httpx.Client(base_url="http://127.0.0.1:8010", timeout=120))
            authenticate(primary, credentials, args.session)
            if args.action == "prepare":
                foreign = authenticated(credentials, "private")
                stack.callback(foreign.close)
                prepare(report, directory, primary, foreign)
            ok = collect(primary, report, directory)
            if verify_runtime() != runtime or snapshot() != frozen:
                raise ValueError("Source/runtime/corpus changed during collection")
            report["status"] = "snapshot_collected" if ok else "collection_failed"
            save(report, directory)
            print(f"Saved {len(report['cases'])} cases; generation quality remains unverified: {directory}")
            return 0 if ok else 1
    except Exception as error:
        report["status"] = "failed"
        report.setdefault("failures", []).append({"type": type(error).__name__, "message": str(error)})
        save(report, directory)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
