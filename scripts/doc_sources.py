"""Safe, deterministic source inventory and per-area documentation fingerprints."""
import hashlib
import json
import os
import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "docs/freshness.json"
RECEIPTS = "docs/freshness-reviews.json"
GENERATED = "docs/generated/source-reference.md"


def safe_path(root, name):
    if not isinstance(name, str):
        raise ValueError("Repository paths must be strings")
    path = PurePosixPath(name)
    if not name or "\\" in name or ":" in name or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe repository path: {name}")
    target = root / name
    if any(part.is_symlink() for part in [target, *target.parents]) or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Unsafe symlink/outside path: {name}")
    return target


def files(root):
    output = subprocess.check_output([
        "git", "-c", f"safe.directory={root.as_posix()}", "-c", f"core.excludesFile={os.devnull}", "ls-files", "--cached",
        "--others", "--exclude-standard", "-z"], cwd=root)
    return sorted({name for name in output.decode("utf-8").split("\0")
                   if name and safe_path(root, name).is_file()})


def normalized(path):
    content = path.read_bytes()
    try:
        return content.decode("utf-8-sig").replace("\r\n", "\n").encode("utf-8")
    except UnicodeDecodeError:
        return content


def load(root, name):
    return json.loads(safe_path(root, name).read_text(encoding="utf-8-sig"))


def matches(name, selectors):
    return any(name.startswith(item) if item.endswith("/") else name == item for item in selectors)


def snapshot(root):
    manifest = load(root, MANIFEST)
    if not isinstance(manifest, dict) or manifest.get("version") != 1 or not isinstance(manifest.get("areas"), dict) or not manifest["areas"]:
        raise ValueError("freshness.json requires version 1 and nonempty areas")
    names = files(root)
    sources = [n for n in names if n not in {MANIFEST, RECEIPTS, GENERATED}]
    errors, areas = [], {}
    for area, config in manifest["areas"].items():
        if not isinstance(config, dict):
            raise ValueError(f"{area}: mapping must be an object")
        selectors, docs = config["sources"], config["docs"]
        if not isinstance(selectors, list) or not isinstance(docs, list) or not selectors or not docs:
            raise ValueError(f"{area}: source selectors and owning docs are required")
        for name in selectors + docs:
            safe_path(root, name)
        selected = [n for n in sources if matches(n, selectors)]
        if not selected:
            errors.append(f"{area}: no source files match; update the area mapping")
        for name in docs:
            if name in {MANIFEST, RECEIPTS, GENERATED} or not name.endswith(".md"):
                raise ValueError(f"{area}: owning documents must be handwritten Markdown: {name}")
            if not safe_path(root, name).is_file():
                errors.append(f"{area}: missing owning document {name}")
        digest = hashlib.sha256(json.dumps({"version": manifest["version"], "area": config}, sort_keys=True).encode())
        for name in sorted(set(selected + docs)):
            digest.update(name.encode() + b"\0")
            path = safe_path(root, name)
            digest.update(normalized(path) if path.is_file() else b"MISSING")
            digest.update(b"\0")
        areas[area] = {"fingerprint": digest.hexdigest(), "sources": selected, "docs": docs}
    for name in sources:
        if not name.endswith(".md") and not any(matches(name, a["sources"]) for a in manifest["areas"].values()):
            errors.append(f"Unmapped source: {name}; add its owning area/docs to {MANIFEST}")
    return areas, errors
