"""Freeze or verify evaluator-only inputs; never consumed by application runtime."""

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "corpus/v1/manifest.json"
CASES = ROOT / "cases/retrieval-v1.json"
FACTS = ROOT / "cases/retrieval-facts-v1.json"
LOCK = ROOT / "corpus/v1/freeze.json"


def snapshot():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    paths = [MANIFEST, CASES, FACTS, ROOT / "corpus/v1/README.md"]
    sections = set()
    active_texts = []
    english_words = cjk = byte_count = 0
    for document in manifest["documents"]:
        path = (ROOT / document["path"]).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError("Corpus path escapes evals")
        source = path.read_text(encoding="utf-8")
        paths.append(path)
        byte_count += len(source.encode("utf-8"))
        english_words += len(re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*", source))
        cjk += len(re.findall(r"[\u3040-\u30ff\u3400-\u9fff]", source))
        if document["state"] == "active":
            sections.update(re.findall(r"(?m)^## (.+)$", source))
            active_texts.append(" ".join(source.split()).casefold())
    if Counter(case["language"] for case in cases) != {"en": 10, "ja": 10, "zh": 10}:
        raise ValueError("Require ten cases per language")
    if len({case["id"] for case in cases}) != len(cases):
        raise ValueError("Duplicate case ID")
    for case in cases:
        if any(not set(group) <= sections for group in case["groups"]):
            raise ValueError("Missing active equivalent section: " + case["id"])
        if bool(case["groups"]) != bool(facts.get(case["id"])):
            raise ValueError("Evidence-bearing cases require frozen factual spans")
        for alternatives in facts.get(case["id"], []):
            if not any(
                " ".join(span.split()).casefold() in text
                for span in alternatives
                for text in active_texts
            ):
                raise ValueError(
                    "Factual span absent from active corpus: " + case["id"]
                )
    pages = english_words / 300 + cjk / 900
    if not 30 <= pages <= 50:
        raise ValueError(f"Corpus outside 30–50 page-equivalent target: {pages:.2f}")
    return {
        "files": {
            path.relative_to(ROOT).as_posix(): hashlib.sha256(
                path.read_text(encoding="utf-8").encode("utf-8")
            ).hexdigest()
            for path in paths
        },
        "source_bytes": byte_count,
        "hash_normalization": "UTF-8 with LF line endings",
        "english_style_words": english_words,
        "cjk_characters": cjk,
        "page_equivalents": round(pages, 2),
        "recall_at": 5,
        "overall_target": 0.9,
        "language_target": 0.8,
        "warm_p95_seconds": 3,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    current = snapshot()
    if args.freeze:
        with LOCK.open("x", encoding="utf-8") as output:
            json.dump(current, output, indent=2, ensure_ascii=False)
    elif current != json.loads(LOCK.read_text(encoding="utf-8")):
        raise ValueError(
            "Frozen corpus changed; do not silently rewrite the acceptance baseline"
        )
    print(json.dumps({key: value for key, value in current.items() if key != "files"}))


if __name__ == "__main__":
    main()
