"""Prepare review material, regenerate facts, and enforce explicit review receipts."""
import argparse
import json
import subprocess

from doc_reference import render
from doc_sources import GENERATED, RECEIPTS, ROOT, load, safe_path, snapshot


def report(root):
    areas, errors = snapshot(root)
    path = safe_path(root, RECEIPTS)
    receipts = load(root, RECEIPTS) if path.exists() else {}
    if not isinstance(receipts, dict) or any(not isinstance(r, dict) for r in receipts.values()):
        raise ValueError("Review receipts must map area names to review objects")
    for name, area in areas.items():
        receipt = receipts.get(name, {})
        area["review"] = receipt
        area["current"] = (receipt.get("fingerprint") == area["fingerprint"]
                           and isinstance(receipt.get("reviewer"), str) and bool(receipt["reviewer"].strip())
                           and isinstance(receipt.get("rationale"), str) and bool(receipt["rationale"].strip())
                           and receipt.get("outcome") in {"updated", "no-doc-impact"})
        if not area["current"]:
            errors.append(f"{name}: stale/missing review; run garden, independently review sources/docs, then acknowledge")
    target = safe_path(root, GENERATED)
    if not target.exists() or target.read_text(encoding="utf-8") != render(root):
        errors.append(f"{GENERATED}: stale/missing; run python scripts/docs_freshness.py generate")
    return {"areas": areas, "errors": errors,
            "notice": "Fingerprints detect change; they do not prove review honesty or semantic accuracy. Review historical/current claims and evidence even when fingerprints match."}


def acknowledge(root, area, fingerprint, reviewer, outcome, rationale):
    areas, errors = snapshot(root)
    if errors:
        raise ValueError("; ".join(errors))
    if area not in areas or areas[area]["fingerprint"] != fingerprint:
        raise ValueError("Unknown area or changed review fingerprint; regenerate garden and review again")
    if not reviewer.strip() or not rationale.strip() or outcome not in {"updated", "no-doc-impact"}:
        raise ValueError("Reviewer, explicit outcome and nonempty review rationale are required")
    path = safe_path(root, RECEIPTS)
    receipts = load(root, RECEIPTS) if path.exists() else {}
    if not isinstance(receipts, dict):
        raise ValueError("Review receipts must map area names to review objects")
    receipts[area] = {"fingerprint": fingerprint, "reviewer": reviewer, "outcome": outcome, "rationale": rationale}
    path.write_text(json.dumps(receipts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "garden", "generate"):
        sub.add_parser(name)
    ack = sub.add_parser("acknowledge", help="Record an already-completed independent semantic review")
    for name in ("area", "fingerprint", "reviewer", "outcome", "rationale"):
        ack.add_argument(f"--{name}", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            target = safe_path(ROOT, GENERATED)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(render(ROOT), encoding="utf-8", newline="\n")
            print(f"Generated {GENERATED}; review receipts were not changed.")
            return 0
        if args.command == "acknowledge":
            acknowledge(ROOT, args.area, args.fingerprint, args.reviewer, args.outcome, args.rationale)
            print(f"Recorded explicit review for {args.area}; no claim of automated semantic proof.")
            return 0
        result = report(ROOT)
        if args.command == "garden":
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
        for error in result["errors"]:
            print(error)
        if not result["errors"]:
            print("Generated facts and area review fingerprints are current; semantic correctness requires review.")
        return int(bool(result["errors"]))
    except (ValueError, OSError, KeyError, StopIteration, SyntaxError, subprocess.CalledProcessError) as exc:
        print(f"Documentation freshness failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
