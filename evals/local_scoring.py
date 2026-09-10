"""Local-live evidence checks; semantic assertions remain separately attributed and bound."""

import hashlib
import json
from collections import Counter

from generation_scoring import PIPELINES, digest, observation


def evidence(item, saved, documents, root, question, language):
    if not item.get("initial_response"):
        return []
    if not saved or not saved.get("request") or not saved.get("response"):
        return ["missing_local_evidence"]
    request, response, context, call = (saved[key] for key in ("request", "response", "context", "call"))
    errors = []
    if context["original"] != question or context["language"] != language:
        errors.append("case_context_identity")
    if request["model"] != item["configuration"]["model"]:
        errors.append("request_model_identity")
    if saved["contributor_id"] is not None or item["contributor_id"] is not None:
        errors.append("machine_attributed_to_human")
    if digest(request) != item["request_hash"] or saved["request_hash"] != item["request_hash"]:
        errors.append("request_identity")
    if (
        response != item["initial_response"]
        or digest({"request_hash": item["request_hash"], "response": response}) != item["response_hash"]
    ):
        errors.append("response_identity")
    if (
        not call
        or call["id"] != request.get("call_id")
        or call["status"] != "succeeded"
        or call["revision"] != item["request_hash"]
        or call["model"] != item["configuration"]["model"]
        or call["job_id"] != item["job_id"]
        or call["provider"] != "local_ollama"
    ):
        errors.append("ledger_identity")
    sources = {source["chunk_id"]: source for source in context["sources"]}
    payload = json.loads(request["messages"][1]["content"])
    expected = [
        {"id": i + 1, "title": s["title"], "text": s["text"]} for i, s in enumerate(context["sources"])
    ]
    if payload != {"question": context["original"], "sources": expected}:
        errors.append("model_context_identity")
    if item["name"] == "direct_llm" and (
        sources or item["retrieval_id"] or request["schema_version"] != "local-direct-v1"
    ):
        errors.append("direct_retrieved_context")
    versions = {document["version_id"]: document for document in documents}
    for source in sources.values():
        document = versions.get(source["version_id"])
        if (
            not document
            or document["spec"]["state"] != "active"
            or document["document_id"] != source["document_id"]
        ):
            errors.append("ineligible_source")
            continue
        path = (root / document["spec"]["path"]).resolve()
        if not path.is_relative_to(root.resolve()):
            errors.append("source_path")
            continue
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        if (
            hashlib.sha256(raw).hexdigest() != source["checksum"]
            or text[source["start_offset"] : source["end_offset"]] != source["text"]
        ):
            errors.append("source_identity")
    seen = set()
    for citation in response["citations"]:
        source = sources.get(citation["chunk_id"])
        if (
            not source
            or not citation["quote"].strip()
            or citation["quote"] not in source["text"]
            or citation["chunk_id"] in seen
        ):
            errors.append("invalid_citation")
        seen.add(citation["chunk_id"])
    if item["name"] != "direct_llm" and response.get("routing", {}).get("decision") == "answer" and not seen:
        errors.append("unsupported_answer")
    return errors


def score(report, cases, snapshots, judgments, root, protocol):
    if (
        report.get("status") != "snapshot_collected"
        or not report.get("runtime")
        or report.get("runtime_after") != report["runtime"]
        or report.get("evidence_hash") != digest(snapshots)
    ):
        raise ValueError("Unfinalized or changed collection evidence")
    expected = [(c["id"], c["question"], c["language"]) for c in cases]
    if len(expected) != 30 or Counter(c[2] for c in expected) != {"en": 10, "ja": 10, "zh": 10}:
        raise ValueError("Frozen30-case input required")
    if (
        report["experiment"] != "local-generation-batch-v1"
        or [(c["id"], c["question"], c["language"]) for c in report["cases"]] != expected
    ):
        raise ValueError("Wrong mode or changed case denominator")
    saved = {(row["comparison_id"], p["name"]): p for row in snapshots for p in row["pipelines"]}
    if len(saved) != sum(len(row["pipelines"]) for row in snapshots):
        raise ValueError("Duplicate evidence")
    reviews = {}
    for judgment in judgments:
        key = judgment["case_id"], judgment["pipeline"]
        if key in reviews or key[0] not in {c[0] for c in expected} or key[1] not in PIPELINES:
            raise ValueError("Duplicate or unknown review")
        if (
            not judgment.get("reviewer", "").strip()
            or judgment.get("kind") not in {"human", "codex_assisted"}
            or len(judgment.get("rationale", "").strip()) < 20
            or set(judgment["checks"]) != set(protocol["checks"])
            or any(type(v) is not bool for v in judgment["checks"].values())
        ):
            raise ValueError("Attributed rationale and boolean checks required")
        reviews[key] = judgment
    results, settings = [], set()
    for row in report["cases"]:
        detail = row.get("detail") or {}
        if detail and (
            detail["id"] != row["comparison_id"]
            or detail["question"] != row["question"]
            or detail["language"] != row["language"]
            or detail["corpus_hash"] != report["corpus_hash"]
        ):
            raise ValueError("Comparison identity changed")
        items = {p["name"]: p for p in detail.get("pipelines", [])}
        if len(items) != len(detail.get("pipelines", [])) or set(items) - set(PIPELINES):
            raise ValueError("Duplicate or unknown pipeline")
        for name in PIPELINES:
            item = items.get(name)
            binding = observation(row, item) if item else None
            judgment = reviews.get((row["id"], name))
            if judgment and judgment["observation_hash"] != binding:
                raise ValueError("Stale review")
            errors = []
            if item:
                config = item["configuration"]
                strategy = {
                    "direct_llm": None,
                    "vector_rag": "vector",
                    "hybrid_rag": "hybrid",
                    "system_v1": "hybrid",
                }[name]
                if config != {
                    "strategy": strategy,
                    "limit": 5,
                    "context_bytes": 24000,
                    "transport": "local_ollama",
                    "version": 2,
                    "model": config.get("model"),
                } or not config.get("model"):
                    raise ValueError("Pipeline configuration differs from local contract")
                record = saved.get((row["comparison_id"], name))
                if record and record.get("request"):
                    request = record["request"]
                    settings.add(digest({k: request[k] for k in ("model", "endpoint", "format", "options")}))
                errors = evidence(item, record, report["documents"], root, row["question"], row["language"])
            eligible = bool(
                item
                and not row["error"]
                and detail.get("comparable")
                and item["state"] in {"completed", "awaiting_review"}
                and (item["initial_response"] or (name == "system_v1" and item.get("outcome") == "set_aside"))
            )
            reviewed = bool(eligible and judgment)
            results.append(
                {
                    "case_id": row["id"],
                    "language": row["language"],
                    "pipeline": name,
                    "observation_hash": binding,
                    "reviewed": reviewed,
                    "passed": bool(reviewed and not errors and all(judgment["checks"].values())),
                    "evidence_errors": errors,
                    "review": judgment,
                }
            )
    if len(settings) > 1:
        raise ValueError("Incompatible model settings")
    totals = {}
    for name in PIPELINES:
        rows = [r for r in results if r["pipeline"] == name]
        groups = {
            lang: {
                "total": len(group),
                "reviewed": sum(r["reviewed"] for r in group),
                "passed": sum(r["passed"] for r in group),
            }
            for lang in ("all", "en", "ja", "zh")
            for group in [[r for r in rows if lang == "all" or r["language"] == lang]]
        }
        gate = all(
            r["reviewed"] and not r["evidence_errors"] and r["review"]["checks"]["no_unsafe_claims"]
            for r in rows
        ) and all(
            g["passed"] * 100
            >= g["total"] * protocol["overall_percent" if lang == "all" else "language_percent"]
            for lang, g in groups.items()
        )
        totals[name] = {"groups": groups, "local_target_met": gate}
    return {
        "protocol_hash": digest(protocol),
        "batch_hash": digest(report),
        "results": results,
        "pipelines": totals,
    }
