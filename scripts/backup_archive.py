"""Validate and copy a trusted local backup before a restoration can mutate PostgreSQL."""
import hashlib
import json
import re

MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
SHA256 = re.compile(r"[a-f0-9]{64}")


def validate_manifest(value):
    if not isinstance(value, dict) or value.get("status") != "passed":
        raise ValueError("Expected a successful standalone backup manifest")
    if (value.get("source_database") != "asi_rebuild"
            or value.get("scope") != "database snapshot export only; restoration not attempted"
            or value.get("restoration_verified") is not False
            or any(key in value for key in ("target_database", "database_created", "parity_verified"))):
        raise ValueError("Manifest does not describe a standalone development backup")
    size, digest = value.get("dump_bytes"), value.get("dump_sha256")
    if type(size) is not int or not 0 < size <= MAX_ARCHIVE_BYTES:
        raise ValueError("Backup archive size must be positive and at most512 MiB")
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        raise ValueError("Backup archive checksum is invalid")
    tables = value.get("source_tables")
    if not isinstance(tables, dict) or not 1 <= len(tables) <= 512:
        raise ValueError("Backup table fingerprints are missing or excessive")
    for name, entry in tables.items():
        if (not re.fullmatch(r"[a-z_][a-z0-9_]*", name) or not isinstance(entry, dict)
                or type(entry.get("rows")) is not int or entry["rows"] < 0
                or not isinstance(entry.get("sha256"), str) or not SHA256.fullmatch(entry["sha256"])):
            raise ValueError("Backup table fingerprint is invalid")
    metadata = value.get("source_metadata")
    if not isinstance(metadata, dict) or set(metadata) != {"extensions", "sequences"}:
        raise ValueError("Backup metadata is missing")
    for field, expected in (("extensions", {"extname": str, "extversion": str}),
                            ("sequences", {"name": str, "last_value": int, "is_called": bool})):
        entries = metadata[field]
        if not isinstance(entries, list) or len(entries) > 512:
            raise ValueError("Backup metadata list is invalid")
        for entry in entries:
            if (not isinstance(entry, dict) or set(entry) != set(expected)
                    or any(type(entry[key]) is not kind for key, kind in expected.items())):
                raise ValueError("Backup metadata entry is invalid")
    return value


def copy_verified_backup(root, requested, destination, remaining):
    root = root.resolve(strict=True)
    allowed = (root / ".artifacts" / "m6").resolve(strict=True)
    directory = (root / requested).resolve(strict=True)
    if (not allowed.is_relative_to(root) or directory.parent != allowed
            or not re.fullmatch(r"backup-\d{8}T\d{6}Z", directory.name)):
        raise ValueError("Select a trusted standalone backup directly under .artifacts/m6")
    manifest_path = (directory / "report.json").resolve(strict=True)
    archive_path = (directory / "snapshot.dump").resolve(strict=True)
    if any(path.parent != directory or not path.is_file() for path in (manifest_path, archive_path)):
        raise ValueError("Backup files must resolve within the selected backup directory")
    with manifest_path.open("rb") as original:
        encoded = original.read(MAX_MANIFEST_BYTES + 1)
    if len(encoded) > MAX_MANIFEST_BYTES:
        raise ValueError("Backup manifest exceeds2 MiB")
    manifest = validate_manifest(json.loads(encoded))
    digest, size = hashlib.sha256(), 0
    with archive_path.open("rb") as original, destination.open("xb") as copied:
        while block := original.read(1024 * 1024):
            remaining()
            size += len(block)
            if size > manifest["dump_bytes"]:
                raise ValueError("Backup archive exceeds its declared size")
            digest.update(block)
            copied.write(block)
    if size != manifest["dump_bytes"] or digest.hexdigest() != manifest["dump_sha256"]:
        raise ValueError("Copied backup archive does not match its manifest")
    with destination.open("rb") as copied:
        copied_digest = hashlib.file_digest(copied, "sha256").hexdigest()
    if destination.stat().st_size != size or copied_digest != digest.hexdigest():
        raise ValueError("Stored backup copy failed verification")
    return {"backup_directory": str(directory.relative_to(root)),
            "backup_manifest_sha256": hashlib.sha256(encoded).hexdigest(),
            "dump_sha256": digest.hexdigest(), "dump_bytes": size,
            "source_tables": manifest["source_tables"], "source_metadata": manifest["source_metadata"]}
