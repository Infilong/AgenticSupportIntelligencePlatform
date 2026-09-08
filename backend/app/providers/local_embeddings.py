"""Real local multilingual embeddings behind LangChain's narrow embedding interface."""

import threading
import time
from dataclasses import dataclass
from pathlib import Path

from langchain_core.embeddings import Embeddings

MODEL = "intfloat/multilingual-e5-small"
REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
DIMENSIONS = 384
MAX_TOKENS = 512


@dataclass(frozen=True)
class EmbeddingBatch:
    vectors: list[list[float]]
    input_tokens: int
    duration_ms: float
    model: str = MODEL
    revision: str = REVISION
    dimensions: int = DIMENSIONS
    provider: str = "local_cpu"
    api_cost_usd: float = 0.0


class LocalEmbeddings(Embeddings):
    def __init__(self, cache_dir: str | Path | None = None, allow_download=False):
        self.cache_dir = str(cache_dir) if cache_dir else None
        self.allow_download = allow_download
        self._model = None
        self._lock = threading.RLock()

    def load(self):
        with self._lock:
            if self._model is None:
                import torch
                from sentence_transformers import SentenceTransformer

                torch.set_num_threads(2)
                self._model = SentenceTransformer(
                    MODEL,
                    revision=REVISION,
                    device="cpu",
                    cache_folder=self.cache_dir,
                    local_files_only=not self.allow_download,
                    trust_remote_code=False,
                    token=False,
                    model_kwargs={"use_safetensors": True},
                )
                if self._model.get_embedding_dimension() != DIMENSIONS:
                    raise ValueError("Embedding model dimension does not match the stored vector space")
            return self._model

    def token_count(self, text: str) -> int:
        return len(self.load().tokenizer.encode(text, add_special_tokens=True))

    def encode_batch(self, texts: list[str], kind: str = "passage") -> EmbeddingBatch:
        if kind not in {"query", "passage"} or not texts or len(texts) > 16:
            raise ValueError("Embedding batch requires 1–16 query or passage inputs")
        started = time.monotonic()
        with self._lock:
            model = self.load()
            prepared = [f"{kind}: {text}" for text in texts]
            counts = [self.token_count(text) for text in prepared]
            if any(count > MAX_TOKENS for count in counts):
                raise ValueError("Embedding input exceeds 512 tokens; split it before dispatch")
            vectors = model.encode(
                prepared, batch_size=16, normalize_embeddings=True, show_progress_bar=False
            ).tolist()
        return EmbeddingBatch(
            vectors=vectors,
            input_tokens=sum(counts),
            duration_ms=round((time.monotonic() - started) * 1000, 2),
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [
            vector
            for start in range(0, len(texts), 16)
            for vector in self.encode_batch(texts[start : start + 16]).vectors
        ]

    def embed_query(self, text: str) -> list[float]:
        return self.encode_batch([text], "query").vectors[0]
