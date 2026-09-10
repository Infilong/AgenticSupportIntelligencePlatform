"""Score retained generation evidence with explicitly attributed, bound review judgments."""

import argparse
import hashlib
import json
from pathlib import Path

from freeze_retrieval import CASES, LOCK, MANIFEST, ROOT, snapshot
from generation_scoring import PIPELINES, score


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument(
        "--judgments", type=Path, required=True, help="JSON array; [] records all cases unreviewed"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    frozen = snapshot()
    report = json.loads((args.directory / "report.json").read_text(encoding="utf-8"))
    if frozen != json.loads(LOCK.read_text(encoding="utf-8")) or report["frozen"] != frozen:
        raise ValueError("Frozen corpus changed")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["documents"]
    if [document["spec"] for document in report["documents"]] != manifest:
        raise ValueError("Batch document identities differ from frozen manifest")
    protocol_bytes = (
        (ROOT / "generation-review-v1.json").read_text(encoding="utf-8").replace("\r\n", "\n").encode()
    )
    expected_hash = (ROOT / "generation-review-v1.sha256").read_text().strip()
    if hashlib.sha256(protocol_bytes).hexdigest() != expected_hash:
        raise ValueError("Frozen generation rubric changed")
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    requests = {}
    for case in cases:
        for name in PIPELINES:
            path = args.directory / "requests" / case["id"] / (name + ".json")
            if path.exists():
                requests[case["id"], name] = json.loads(path.read_text(encoding="utf-8"))
    result = score(
        report,
        cases,
        json.loads(args.judgments.read_text(encoding="utf-8")),
        requests,
        report["documents"],
        ROOT,
        json.loads(protocol_bytes),
    )
    result["scorer_sha256"] = hashlib.sha256((ROOT / "generation_scoring.py").read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
    print(f"Saved120 case/pipeline observations to {args.output}; live generation quality is not verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
