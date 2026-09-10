"""Source-bound structural checks and explicit attributed semantic-review aggregation."""

import hashlib
import json
from collections import Counter

PIPELINES = ("direct_llm", "vector_rag", "hybrid_rag", "system_v1")


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def observation(row, item):
    return digest(
        {
            "case": row["id"],
            "question": row["question"],
            "language": row["language"],
            "comparison": row["comparison_id"],
            "corpus": row["detail"]["corpus_hash"],
            "pipeline": item["name"],
            "configuration": item["configuration"],
            "request_hash": item.get("request_hash"),
            "response_hash": item.get("response_hash"),
            "response": item.get("initial_response"),
            "contributor": item.get("contributor_id"),
            "outcome": item.get("outcome"),
            "state": item["state"],
        }
    )


def evidence(item, request, documents, source_root):
    response = item.get("initial_response")
    if not response:
        return []
    errors = []
    if not request or digest(request["generation_request"]) != item["request_hash"]:
        return ["request_identity"]
    if (
        request["request_hash"] != item["request_hash"]
        or response.get("request_hash") != item["request_hash"]
    ):
        errors.append("response_request_identity")
    if response.get("context_hash") != request["context_hash"]:
        errors.append("response_context_identity")
    if (
        not item.get("contributor_id")
        or digest({"contributor": item["contributor_id"], "response": response}) != item["response_hash"]
    ):
        errors.append("response_identity")
    payload = json.loads(request["generation_request"]["messages"][1]["content"])
    sources = {source["chunk_id"]: source for source in payload["sources"]}
    versions = {document["version_id"]: document for document in documents}
    if item["name"] == "direct_llm" and sources:
        errors.append("direct_retrieved_context")
    for source in sources.values():
        document = versions.get(source["version_id"])
        if (
            not document
            or document["spec"]["state"] != "active"
            or document["document_id"] != source["document_id"]
        ):
            errors.append("ineligible_source")
            continue
        path = (source_root / document["spec"]["path"]).resolve()
        if not path.is_relative_to(source_root.resolve()):
            errors.append("source_path")
            continue
        raw = path.read_bytes()
        normalized = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        if (
            hashlib.sha256(raw).hexdigest() != source["checksum"]
            or normalized[source["start_offset"] : source["end_offset"]] != source["text"]
        ):
            errors.append("source_identity")
    seen = set()
    citations = response.get("citations", [])
    if not citations and item["name"] != "direct_llm":
        errors.append("missing_citations")
    for citation in citations:
        source = sources.get(citation["chunk_id"])
        quote = citation["quote"]
        if not source or not quote.strip() or quote not in source["text"] or citation["chunk_id"] in seen:
            errors.append("invalid_citation")
        seen.add(citation["chunk_id"])
    return sorted(set(errors))


def score(report, cases, judgments, requests, documents, source_root, protocol):
    if (
        report.get("experiment") != "generation-batch-v1"
        or report.get("status") != "snapshot_collected"
        or report.get("corpus_ready") is not True
        or set(report.get("runtime", {})) != {"api", "worker"}
    ):
        raise ValueError("A successfully validated batch envelope is required")
    expected = [(case["id"], case["question"], case["language"]) for case in cases]
    if len(expected) != 30 or Counter(case[2] for case in expected) != {"en": 10, "ja": 10, "zh": 10}:
        raise ValueError("Frozen30-case/10-per-language input required")
    if [(row["id"], row["question"], row["language"]) for row in report["cases"]] != expected:
        raise ValueError("Report cases differ from frozen cases")
    reviews = {}
    for judgment in judgments:
        key = (judgment["case_id"], judgment["pipeline"])
        if key in reviews or key[0] not in {case[0] for case in expected} or key[1] not in PIPELINES:
            raise ValueError("Duplicate or unknown review")
        if (
            not judgment.get("reviewer", "").strip()
            or judgment.get("kind") not in {"human", "codex_assisted"}
            or len(judgment.get("rationale", "").strip()) < 20
            or set(judgment["checks"]) != set(protocol["checks"])
            or any(type(value) is not bool for value in judgment["checks"].values())
        ):
            raise ValueError("Attributed rationale and exact boolean review checks required")
        reviews[key] = judgment
    results = []
    for row in report["cases"]:
        detail = row.get("detail") or {}
        if detail and (
            detail["id"] != row["comparison_id"]
            or detail["question"] != row["question"]
            or detail["language"] != row["language"]
            or detail["corpus_hash"] != report["corpus_hash"]
        ):
            raise ValueError("Comparison identity or shared corpus changed")
        items = {item["name"]: item for item in detail.get("pipelines", [])}
        if len(items) != len(detail.get("pipelines", [])) or set(items) - set(PIPELINES):
            raise ValueError("Duplicate or unknown pipeline")
        for name, item in items.items():
            expected_config = {
                "strategy": {
                    "direct_llm": None,
                    "vector_rag": "vector",
                    "hybrid_rag": "hybrid",
                    "system_v1": "hybrid",
                }[name],
                "limit": 5,
                "context_bytes": 24000,
                "transport": "attributed_development",
                "version": 1,
            }
            if item.get("configuration") != expected_config:
                raise ValueError("Pipeline configuration differs from frozen contract")
        for name in PIPELINES:
            item = items.get(name)
            errors = []
            judgment = reviews.get((row["id"], name))
            binding = observation(row, item) if item else None
            if judgment and judgment["observation_hash"] != binding:
                raise ValueError("Review belongs to a different observation")
            if item:
                errors = evidence(item, requests.get((row["id"], name)), documents, source_root)
            eligible = bool(
                item
                and (
                    item.get("initial_response")
                    or (
                        name == "system_v1"
                        and item["state"] == "completed"
                        and item.get("outcome") in {"clarification_needed", "insufficient_evidence"}
                    )
                )
            )
            eligible = eligible and not row["error"] and detail.get("comparable") is True
            eligible = eligible and item["state"] not in {
                "failed",
                "cancelled",
                "queued",
                "running",
                "waiting_for_input",
            }
            reviewed = bool(eligible and judgment)
            passed = bool(reviewed and not errors and all(judgment["checks"].values()))
            results.append(
                {
                    "case_id": row["id"],
                    "language": row["language"],
                    "pipeline": name,
                    "observation_hash": binding,
                    "reviewed": reviewed,
                    "passed": passed,
                    "evidence_errors": errors,
                    "review": judgment,
                }
            )
    totals = {}
    for name in PIPELINES:
        selected = [result for result in results if result["pipeline"] == name]
        groups = {}
        for language in ("all", "en", "ja", "zh"):
            group = [result for result in selected if language == "all" or result["language"] == language]
            groups[language] = {
                "total": len(group),
                "reviewed": sum(row["reviewed"] for row in group),
                "passed": sum(row["passed"] for row in group),
            }
        complete = all(row["reviewed"] for row in selected)
        safe = all(not row["review"] or row["review"]["checks"]["no_unsafe_claims"] for row in selected)
        gate = (
            complete
            and safe
            and not any(row["evidence_errors"] for row in selected)
            and all(
                group["passed"] * 100
                >= group["total"] * protocol["overall_percent" if lang == "all" else "language_percent"]
                for lang, group in groups.items()
            )
        )
        totals[name] = {"groups": groups, "development_target_met": gate}
    return {
        "protocol_hash": digest(protocol),
        "batch_hash": digest(report),
        "results": results,
        "pipelines": totals,
        "live_generation_quality": "not_verified",
    }
