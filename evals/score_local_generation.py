"""Score local-live evidence with frozen thresholds and separately attributed judgments."""

import argparse
import hashlib
import json
from pathlib import Path

from freeze_retrieval import CASES, LOCK, MANIFEST, ROOT, snapshot
from local_scoring import score


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--judgments", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads((args.directory / "report.json").read_text(encoding="utf-8"))
    frozen = snapshot()
    if frozen != json.loads(LOCK.read_text(encoding="utf-8")) or report["frozen"] != frozen:
        raise ValueError("Frozen corpus changed")
    if [d["spec"] for d in report["documents"]] != json.loads(MANIFEST.read_text(encoding="utf-8"))[
        "documents"
    ]:
        raise ValueError("Batch documents differ from frozen manifest")
    raw = (
        (ROOT / "generation-review-local-v1.json").read_text(encoding="utf-8").replace("\r\n", "\n").encode()
    )
    if hashlib.sha256(raw).hexdigest() != (ROOT / "generation-review-local-v1.sha256").read_text().strip():
        raise ValueError("Frozen local rubric changed")
    result = score(
        report,
        json.loads(CASES.read_text(encoding="utf-8")),
        json.loads((args.directory / "local-evidence.json").read_text(encoding="utf-8")),
        json.loads(args.judgments.read_text(encoding="utf-8")),
        ROOT,
        json.loads(raw),
    )
    result["scorer_sha256"] = hashlib.sha256((ROOT / "local_scoring.py").read_bytes()).hexdigest()
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
    print(json.dumps(result["pipelines"], ensure_ascii=False))


if __name__ == "__main__":
    main()
