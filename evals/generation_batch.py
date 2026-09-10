"""Resumable admission and evidence collection; evaluator expectations never reach the app."""

import json
import uuid
from collections import Counter

PIPELINES = ("direct_llm", "vector_rag", "hybrid_rag", "system_v1")


def case_rows(cases):
    return [
        {
            "id": case["id"],
            "question": case["question"],
            "language": case["language"],
            "key": uuid.uuid4().hex,
            "comparison_id": None,
            "detail": None,
            "error": None,
            "failures": [],
        }
        for case in cases
    ]


def summary(rows):
    result = {}
    for language in ("all", "en", "ja", "zh"):
        selected = [row for row in rows if language == "all" or row["language"] == language]
        pipelines = {}
        for name in PIPELINES:
            states = Counter()
            for row in selected:
                item = next(
                    (p for p in (row.get("detail") or {}).get("pipelines", []) if p["name"] == name), None
                )
                states[item["state"] if item else "not_observed"] += 1
            pipelines[name] = dict(states)
        result[language] = {
            "denominator": len(selected),
            "pipelines": pipelines,
            "collection_errors": sum(bool(row["error"]) for row in selected),
        }
    return result


def save(report, directory):
    report["summary"] = summary(report["cases"])
    temporary = directory / "report.tmp"
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(directory / "report.json")


def validate_detail(row, detail, corpus_hash):
    if (
        str(detail["id"]) != row["comparison_id"]
        or detail["question"] != row["question"]
        or detail["language"] != row["language"]
    ):
        raise ValueError("Comparison identity differs from frozen case")
    if not detail["comparable"] or (corpus_hash and detail["corpus_hash"] != corpus_hash):
        raise ValueError("Comparison corpus changed or comparison cancelled")
    items = detail["pipelines"]
    if len(items) != 4 or {item["name"] for item in items} != set(PIPELINES):
        raise ValueError("Four pipeline results required")
    for item in items:
        expected = {
            "strategy": {
                "direct_llm": None,
                "vector_rag": "vector",
                "hybrid_rag": "hybrid",
                "system_v1": "hybrid",
            }[item["name"]],
            "limit": 5,
            "context_bytes": 24000,
            "transport": "attributed_development",
            "version": 1,
        }
        if item["configuration"] != expected:
            raise ValueError("Pipeline configuration differs from frozen batch contract")


def collect(client, report, directory):
    endpoint = f"/api/workspaces/{report['workspaces']['primary']}/comparisons"
    for row in report["cases"]:
        row["error"] = None
        try:
            if not row["comparison_id"]:
                response = client.post(
                    endpoint,
                    json={"original": row["question"], "language": row["language"]},
                    headers={"Idempotency-Key": row["key"]},
                )
                response.raise_for_status()
                row["comparison_id"] = response.json()["id"]
                save(report, directory)
            path = f"{endpoint}/{row['comparison_id']}"
            response = client.get(path)
            response.raise_for_status()
            detail = response.json()
            validate_detail(row, detail, report.get("corpus_hash"))
            report["corpus_hash"] = detail["corpus_hash"]
            row["detail"] = detail
            for item in detail["pipelines"]:
                if item["state"] != "waiting_for_input":
                    continue
                response = client.get(f"{path}/{item['name']}/request")
                response.raise_for_status()
                request = response.json()
                target = directory / "requests" / row["id"] / (item["name"] + ".json")
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    if json.loads(target.read_text(encoding="utf-8")) != request:
                        raise ValueError("Prepared request changed; preserved original export")
                else:
                    temporary = target.with_suffix(".tmp")
                    temporary.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
                    temporary.replace(target)
        except Exception as error:
            # Failures are retained per case, included in denominators and produce a nonzero exit.
            row["error"] = {"type": type(error).__name__, "message": str(error)}
            row["failures"].append(row["error"])
        save(report, directory)
        print(f"{row['id']}: {'collection failed' if row['error'] else 'collected'}", flush=True)
    return not any(row["error"] for row in report["cases"])
