"""Backup exports must never cross into restoration or claim recovery proof."""

import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def drill(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[3] / "scripts" / "restore_drill.py"
    monkeypatch.syspath_prepend(str(path.parent))
    spec = importlib.util.spec_from_file_location("backup_boundary_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    (tmp_path / ".env").write_text("ASI_DATABASE_PASSWORD=synthetic-test-only\n", encoding="utf-8")
    engine = MagicMock()
    connection = engine.connect.return_value.execution_options.return_value.__enter__.return_value
    connection.scalar.return_value = "00000001-00000002-1"
    create = MagicMock(return_value=engine)
    monkeypatch.setattr(module, "create_engine", create)
    monkeypatch.setattr(
        module, "fingerprints", lambda connection: {"example": {"rows": 1, "sha256": "a" * 64}}
    )
    monkeypatch.setattr(module, "metadata", lambda connection: {"extensions": [], "sequences": []})
    exercise = MagicMock()
    monkeypatch.setattr(module, "exercise", exercise)
    commands = []

    def docker(*arguments, **options):
        commands.append(arguments)
        if arguments[0] == "inspect":
            return SimpleNamespace(stdout="asi-rebuild-v1 true")
        if "pg_dump" in arguments:
            options["stdout"].write(b"synthetic archive")
            return SimpleNamespace(returncode=0)
        if "createdb" in arguments or "pg_restore" in arguments:
            return SimpleNamespace(returncode=0)
        raise AssertionError(f"Unexpected Docker operation: {arguments}")

    monkeypatch.setattr(module, "docker", docker)
    return SimpleNamespace(module=module, create=create, exercise=exercise, commands=commands)


def report(drill, mode):
    paths = list((drill.module.ROOT / ".artifacts" / "m6").glob(f"{mode}-*/report.json"))
    assert len(paths) == 1
    return json.loads(paths[0].read_text(encoding="utf-8"))


def test_backup_does_not_create_restore_or_exercise_database(drill, capsys):
    assert drill.module.main(backup_only=True) == 0
    value = report(drill, "backup")
    assert value["status"] == "passed" and value["dump_bytes"] > 0
    assert len(value["dump_sha256"]) == 64
    assert value["restoration_verified"] is False
    assert not {"target_database", "database_created", "restored_tables", "parity_verified"} & value.keys()
    assert len(drill.commands) == 2
    assert drill.commands[0][0] == "inspect" and "pg_dump" in drill.commands[1]
    drill.create.assert_called_once()
    drill.exercise.assert_not_called()
    assert "restoration not attempted" in capsys.readouterr().out


@pytest.mark.parametrize("failure", ["partial", "empty"])
def test_failed_export_leaves_failed_report_without_restoration(drill, monkeypatch, failure):
    original = drill.module.docker

    def export(*arguments, **options):
        if "pg_dump" in arguments:
            if failure == "partial":
                options["stdout"].write(b"partial")
                raise subprocess.CalledProcessError(1, "pg_dump")
            return SimpleNamespace(returncode=0)
        return original(*arguments, **options)

    monkeypatch.setattr(drill.module, "docker", export)
    expected = subprocess.CalledProcessError if failure == "partial" else RuntimeError
    with pytest.raises(expected):
        drill.module.main(backup_only=True)
    value = report(drill, "backup")
    assert value["status"] == "failed" and value["restoration_verified"] is False
    assert value["error_type"] == expected.__name__
    assert "database_created" not in value
    assert len(drill.commands) == 1
    drill.exercise.assert_not_called()
    drill.create.assert_called_once()


def test_default_mode_still_restores_checks_parity_and_exercises(drill):
    assert drill.module.main() == 0
    value = report(drill, "restore")
    assert value["status"] == "passed" and value["parity_verified"] is True
    assert value["database_created"] is True
    assert value["source_tables"] == value["restored_tables"]
    assert any("createdb" in command for command in drill.commands)
    assert any("pg_restore" in command for command in drill.commands)
    assert drill.create.call_count == 2
    drill.exercise.assert_called_once()


def test_saved_archive_skips_source_connection_and_export(drill):
    assert drill.module.main(backup_only=True) == 0
    backup = next((drill.module.ROOT / ".artifacts" / "m6").glob("backup-*"))
    drill.commands.clear()
    drill.create.reset_mock()
    assert drill.module.main(backup_dir=backup) == 0
    value = report(drill, "restore-saved")
    assert value["status"] == "passed" and value["parity_verified"] is True
    assert value["source_tables"] == report(drill, "backup")["source_tables"]
    assert "snapshot" not in value
    assert not any("pg_dump" in command for command in drill.commands)
    drill.create.assert_called_once()
    assert "/asi_restore_" in drill.create.call_args.args[0]
    drill.exercise.assert_called_once()


def test_corrupt_saved_archive_fails_before_any_database_connection_or_creation(drill):
    assert drill.module.main(backup_only=True) == 0
    backup = next((drill.module.ROOT / ".artifacts" / "m6").glob("backup-*"))
    (backup / "snapshot.dump").write_bytes(b"corrupt archive")
    drill.commands.clear()
    drill.create.reset_mock()
    with pytest.raises(ValueError, match="does not match"):
        drill.module.main(backup_dir=backup)
    value = report(drill, "restore-saved")
    assert value["status"] == "failed" and "database_created" not in value
    assert len(drill.commands) == 1 and drill.commands[0][0] == "inspect"
    drill.create.assert_not_called()
    drill.exercise.assert_not_called()
