"""Enforce source size limits without allowing existing oversized files to grow."""

import argparse
import json
import sys
from pathlib import Path

SOURCE_ROOTS = ("backend/app", "frontend/src")
SOURCE_SUFFIXES = {".py", ".ts", ".tsx"}
MAX_LINES = 300
BASELINE = "scripts/source-size-baseline.json"


def collect_sizes(root: Path) -> dict[str, int]:
    sizes = {}
    for source_root in SOURCE_ROOTS:
        directory = root / source_root
        if not directory.is_dir():
            raise ValueError(f"Missing source directory: {source_root}")
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix in SOURCE_SUFFIXES:
                sizes[path.relative_to(root).as_posix()] = len(
                    path.read_text(encoding="utf-8-sig").splitlines()
                )
    return sizes


def read_baseline(path: Path) -> dict[str, int]:
    baseline = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(baseline, dict) or any(
        not isinstance(name, str) or type(limit) is not int or limit <= MAX_LINES
        for name, limit in baseline.items()
    ):
        raise ValueError("Baseline must map source paths to integer limits above 300.")
    return baseline


def violations(sizes: dict[str, int], baseline: dict[str, int]) -> list[str]:
    errors = []
    for name, limit in sorted(baseline.items()):
        if name not in sizes:
            errors.append(f"{name}: remove stale baseline entry; source no longer exists.")
        elif sizes[name] <= MAX_LINES:
            errors.append(f"{name}: now within 300 lines; remove its baseline exception.")
        elif sizes[name] < limit:
            errors.append(f"{name}: lower baseline from {limit} to {sizes[name]} to retain progress.")
    for name, count in sorted(sizes.items()):
        limit = baseline.get(name, MAX_LINES)
        if count > limit:
            errors.append(
                f"{name}: {count} lines exceeds {limit}; split by responsibility "
                "instead of increasing the baseline."
            )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        sizes = collect_sizes(args.root)
        errors = violations(sizes, read_baseline(args.root / BASELINE))
    except (OSError, ValueError) as exc:
        print(f"Source size check could not run: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("Source size check failed:\n" + "\n".join(errors), file=sys.stderr)
        return 1
    print(f"Source size check passed: {len(sizes)} files; {MAX_LINES}-line default.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
