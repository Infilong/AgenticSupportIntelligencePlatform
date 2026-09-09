"""Shared lazy embedding configuration, independent of document-ingestion imports."""

from functools import lru_cache

from app.core.settings import Settings
from app.providers.local_embeddings import MODEL, REVISION, LocalEmbeddings

SPACE = f"{MODEL}:{REVISION}:normalized-query-passage-v1"


@lru_cache(maxsize=1)
def embeddings():
    return LocalEmbeddings(Settings().embedding_cache)
