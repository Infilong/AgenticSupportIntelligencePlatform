"""Compare five explicit strategies on one freshly ingested frozen development corpus."""

import json
import subprocess
import time
from datetime import UTC, datetime

from comparison_metrics import (
    STRATEGIES,
    TRACE_VALIDATOR_VERSION,
    discovery,
    paired,
    summarize,
    trace_valid,
)
from freeze_retrieval import CASES, FACTS, LOCK, MANIFEST, ROOT, snapshot
from retrieval_scoring import SCORER_VERSION, score_case
from run_retrieval import authenticated, ingest, source_state
from runtime_fingerprint import verify_runtime


def measured(client, endpoint, case, strategy, facts, versions):
    started = time.monotonic()
    response = client.post(
        endpoint, json={"query": case["question"], "limit": 5, "strategy": strategy}
    )
    elapsed = time.monotonic() - started
    response.raise_for_status()
    data = response.json()
    trace_response = client.get(f"{endpoint}/{data['trace_id']}")
    trace_response.raise_for_status()
    trace = trace_response.json()
    return {
        **case,
        **score_case(case, data, facts, versions),
        "elapsed_seconds": elapsed,
        "response": data,
        "trace": trace,
        "trace_valid": trace_valid(trace, strategy)
        and [
            row["chunk_id"]
            for row in sorted(
                [row for row in trace["candidates"] if row["final_rank"] is not None],
                key=lambda row: row["final_rank"],
            )
        ]
        == [row["chunk_id"] for row in data["results"]],
        "candidate_leakage": [
            row["version_id"]
            for row in trace["candidates"]
            if versions.get(row["version_id"], {}).get("state") != "active"
        ],
        "section_group_discovery": discovery(case, trace, versions),
        "workflow_outcome": "not_verified",
    }


def main():
    frozen = snapshot()
    if frozen != json.loads(LOCK.read_text(encoding="utf-8")):
        raise ValueError("Frozen evaluation inputs changed")
    artifact = (
        ROOT.parent
        / ".artifacts/m2"
        / ("strategy-comparison-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    )
    artifact.mkdir(parents=True)
    report = {
        "experiment": "retrieval-strategies-v1",
        "status": "started",
        "frozen": frozen,
        "scorer_version": SCORER_VERSION,
        "trace_validator_version": TRACE_VALIDATOR_VERSION,
        "source_state": source_state(),
        "documents": [],
        "strategies": {
            name: {"cases": [], "negative_probes": []} for name in STRATEGIES
        },
        "execution_order": [],
        "generation": "not_verified",
        "default_changed": False,
        "limitations": "Development corpus; pooled required-heading facts are not source-bound entailment. Candidate group discovery is not fact sufficiency. One warm sample per case is not a production latency SLO.",
    }

    def save():
        (artifact / "report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    clients = []
    save()
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
                    "ingestion_seconds": time.monotonic() - started,
                }
            )
            save()
            print("Indexed " + spec["id"], flush=True)
        cases = json.loads(CASES.read_text(encoding="utf-8"))
        facts = json.loads(FACTS.read_text(encoding="utf-8"))
        endpoint = f"/api/workspaces/{workspaces['primary']}/retrieval"
        for strategy in STRATEGIES:
            primary.post(
                endpoint,
                json={"query": cases[0]["question"], "limit": 5, "strategy": strategy},
            ).raise_for_status()
        for index, case in enumerate(cases):
            order = STRATEGIES[index % 5 :] + STRATEGIES[: index % 5]
            for strategy in order:
                report["current_request"] = {"case": case["id"], "strategy": strategy}
                save()
                result = measured(primary, endpoint, case, strategy, facts, versions)
                report["strategies"][strategy]["cases"].append(result)
                report["execution_order"].append(
                    {"case": case["id"], "strategy": strategy}
                )
                save()
                print(
                    f"{case['id']} {strategy}: {result['retrieval_passed']} ({result['elapsed_seconds']:.3f}s)",
                    flush=True,
                )
        probes = (
            "Fifteen-minute lunar research travel approval response and five-day refund window",
            "Private partner refund deadline 365 days and export download 99 days",
        )
        for strategy in STRATEGIES:
            item = report["strategies"][strategy]
            for index, query in enumerate(probes):
                item["negative_probes"].append(
                    measured(
                        primary,
                        endpoint,
                        {"id": f"probe-{index}", "question": query, "groups": []},
                        strategy,
                        {},
                        versions,
                    )
                )
            denied = primary.post(
                f"/api/workspaces/{workspaces['foreign']}/retrieval",
                json={"query": "refund deadline", "limit": 5, "strategy": strategy},
            ).status_code
            item["foreign_request_status"] = denied
            item.update(summarize(item["cases"], item["negative_probes"], denied))
            item["paired_vs_vector_rerank"] = paired(
                item["cases"], report["strategies"]["vector_rerank"]["cases"]
            )
            save()
        report["source_state_after"] = source_state()
        report["runtime_after"] = verify_runtime()
        report["source_unchanged"] = (
            report["source_state"]["source_sha256"]
            == report["source_state_after"]["source_sha256"]
        )
        report["runtime_unchanged"] = report["runtime"] == report["runtime_after"]
        report["status"] = "completed"
        report["experiment_valid"] = (
            report["source_unchanged"]
            and report["runtime_unchanged"]
            and all(len(item["cases"]) == 30 for item in report["strategies"].values())
        )
        save()
        print(
            json.dumps(
                {
                    "artifact": str(artifact),
                    "experiment_valid": report["experiment_valid"],
                    "strategies": {
                        name: {
                            key: value
                            for key, value in item.items()
                            if key not in {"cases", "negative_probes"}
                        }
                        for name, item in report["strategies"].items()
                    },
                },
                ensure_ascii=False,
            )
        )
        return 0 if report["experiment_valid"] else 1
    except Exception as error:
        report.update(status="failed", error_class=type(error).__name__)
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
