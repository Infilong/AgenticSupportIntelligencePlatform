"""Retrieval startup must not initialize the document parsing/model execution stack."""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


def test_retrieval_import_does_not_load_ingestion_or_torch():
    command = (
        "import sys; from app.modules.identity import models; import app.modules.knowledge.retrieval; "
        "from app.modules.usage.models import ModelCall; "
        "assert all(key.column is not None for key in ModelCall.__table__.foreign_keys); "
        "forbidden={'app.modules.knowledge.ingestion','app.modules.knowledge.splitting',"
        "'torch','transformers','sentence_transformers'}; "
        "assert not forbidden.intersection(sys.modules), sorted(forbidden.intersection(sys.modules))"
    )
    result = subprocess.run(
        [sys.executable, "-c", command],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")


def test_embedding_factory_retains_first_call_configuration_without_loading_model(monkeypatch, tmp_path):
    from app.providers import local_models

    observations = []

    def settings():
        observations.append(True)
        return SimpleNamespace(embedding_cache=tmp_path)

    local_models.embeddings.cache_clear()
    monkeypatch.setattr(local_models, "Settings", settings)
    try:
        assert observations == []
        first = local_models.embeddings()
        assert first is local_models.embeddings()
        assert observations == [True] and first.cache_dir == str(tmp_path)
        assert first._model is None
    finally:
        local_models.embeddings.cache_clear()
