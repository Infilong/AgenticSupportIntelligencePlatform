"""Saved archive preflight rejects corruption and escaped paths before database work."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backup_archive import copy_verified_backup, validate_manifest


class BackupArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.backup = self.root / ".artifacts/m6/backup-20260909T135747Z"
        self.backup.mkdir(parents=True)
        self.body = b"a trusted synthetic archive"
        self.value = {
            "status": "passed", "source_database": "asi_rebuild",
            "scope": "database snapshot export only; restoration not attempted",
            "restoration_verified": False,
            "dump_bytes": len(self.body), "dump_sha256": hashlib.sha256(self.body).hexdigest(),
            "source_tables": {"messages": {"rows": 3, "sha256": "a" * 64}},
            "source_metadata": {"extensions": [], "sequences": []},
        }
        (self.backup / "snapshot.dump").write_bytes(self.body)
        (self.backup / "report.json").write_text(json.dumps(self.value), encoding="utf-8")
        self.destination = self.root / "verified-copy.dump"

    def copy(self):
        return copy_verified_backup(self.root, self.backup, self.destination, lambda: 60)

    def test_valid_copy_preserves_original_and_saved_fingerprints(self):
        result = self.copy()
        self.assertEqual(self.destination.read_bytes(), self.body)
        self.assertEqual((self.backup / "snapshot.dump").read_bytes(), self.body)
        self.assertEqual(result["source_tables"], self.value["source_tables"])
        self.assertEqual(result["dump_sha256"], self.value["dump_sha256"])
        self.assertIn("backup_manifest_sha256", result)

    def test_invalid_manifest_fields_are_rejected(self):
        invalid = [("status", "failed"), ("source_database", "other"), ("restoration_verified", True),
                   ("target_database", "anything"), ("dump_bytes", True), ("dump_bytes", 0),
                   ("dump_bytes", 513 * 1024 * 1024), ("dump_sha256", "invalid"),
                   ("source_tables", {}), ("source_tables", {"messages": {"rows": -1, "sha256": "a" * 64}}),
                   ("source_metadata", {}), ("source_metadata", {"extensions": [False], "sequences": []})]
        for field, value in invalid:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                validate_manifest({**self.value, field: value})

    def test_missing_or_corrupt_archive_is_rejected(self):
        (self.backup / "snapshot.dump").unlink()
        with self.assertRaises(FileNotFoundError):
            self.copy()
        (self.backup / "snapshot.dump").write_bytes(b"bad")
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.copy()

    def test_selected_directory_outside_backup_root_is_rejected(self):
        self.backup = self.root
        with self.assertRaises(ValueError):
            self.copy()

    def test_resolved_file_escape_is_rejected(self):
        original = Path.resolve
        escaped = self.root / "outside.dump"
        escaped.write_bytes(self.body)

        def resolve(path, *args, **kwargs):
            return escaped if path.name == "snapshot.dump" else original(path, *args, **kwargs)

        with patch.object(Path, "resolve", resolve), self.assertRaisesRegex(ValueError, "resolve within"):
            self.copy()
        self.assertFalse(self.destination.exists())

    def test_copy_readback_mismatch_and_existing_destination_are_rejected(self):
        with patch("backup_archive.hashlib.file_digest") as digest:
            digest.return_value.hexdigest.return_value = "0" * 64
            with self.assertRaisesRegex(ValueError, "Stored backup copy"):
                self.copy()
        with self.assertRaises(FileExistsError):
            self.copy()

    def test_oversize_manifest_is_rejected(self):
        (self.backup / "report.json").write_bytes(b" " * (2 * 1024 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, "manifest exceeds"):
            self.copy()
