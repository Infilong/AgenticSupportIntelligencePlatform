"""Validate fixture references, not retrieval accuracy or model answer quality."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTCOMES = {"grounded_draft", "clarification_needed", "insufficient_evidence",
            "policy_review_required", "conflicting_evidence"}


def validate(manifest, cases, directory):
    errors = []
    documents = {}
    active = Counter()
    for doc in manifest["documents"]:
        key = (doc["id"], doc["version"])
        if key in documents:
            errors.append(f"Duplicate document version: {key}")
        path = (directory / doc["path"]).resolve()
        if not path.is_relative_to(directory.resolve()) or not path.is_file():
            errors.append(f"Invalid source path: {doc['id']}")
            continue
        documents[key] = (doc, path.read_text(encoding="utf-8"))
        if doc["active"]:
            active[doc["id"]] += 1
    if any(count > 1 for count in active.values()):
        errors.append("Multiple active versions of one document")
    seen = set()
    for case in cases:
        if case["id"] in seen:
            errors.append(f"Duplicate case: {case['id']}")
        seen.add(case["id"])
        if case["language"] not in {"en", "ja", "zh"} or case["outcome"] not in OUTCOMES:
            errors.append(f"Invalid language/outcome: {case['id']}")
        if not case["question"].strip():
            errors.append(f"Blank question: {case['id']}")
        if case["outcome"] in {"grounded_draft", "policy_review_required"} and not case["sources"]:
            errors.append(f"Missing expected evidence: {case['id']}")
        for source in case["sources"]:
            match = documents.get((source["id"], source["version"]))
            if not match or not match[0]["active"]:
                errors.append(f"Missing/inactive source: {case['id']}")
            elif f"## {source['section']}\n" not in match[1]:
                errors.append(f"Missing section: {case['id']}")
    return errors


def load():
    directory = ROOT / "evals" / "fixtures"
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    cases = json.loads((ROOT / "evals" / "cases" / "m0.json").read_text(encoding="utf-8"))
    return manifest, cases, directory
