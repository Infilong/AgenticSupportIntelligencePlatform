"""Bounded real CPU query/passage scoring; no generation or answer fixtures."""

import math
import threading
import time
from dataclasses import dataclass
from functools import lru_cache

from app.core.settings import Settings

MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
REVISION = "1427fd652930e4ba29e8149678df786c240d8825"
MAX_CANDIDATES = 20


class InvalidRerankResult(RuntimeError):
    """An internal model result failure, never a user query validation failure."""


@dataclass(frozen=True)
class RerankBatch:
    scores: list[float]
    input_tokens: int
    duration_ms: float


class LocalReranker:
    def __init__(self, cache_dir=None, allow_download=False):
        self.cache_dir = cache_dir
        self.allow_download = allow_download
        self._model = None
        self._lock = threading.RLock()

    def load(self):
        with self._lock:
            if self._model is None:
                import torch
                from sentence_transformers import CrossEncoder

                torch.set_num_threads(2)
                self._model = CrossEncoder(
                    MODEL,
                    revision=REVISION,
                    device="cpu",
                    cache_folder=self.cache_dir,
                    local_files_only=not self.allow_download,
                    trust_remote_code=False,
                    token=False,
                    max_length=512,
                    model_kwargs={"use_safetensors": True},
                )
            return self._model

    def score(self, query, passages):
        if not query or len(query) > 1000 or not 1 <= len(passages) <= MAX_CANDIDATES:
            raise ValueError("Reranking requires a bounded query and 1–20 passages")
        if any(not text or len(text) > 8000 for text in passages):
            raise ValueError("Reranking passage exceeds the source block bound")
        started = time.monotonic()
        with self._lock:
            model = self.load()
            pairs = [(query, text) for text in passages]
            # CrossEncoder scores at most 512 pair tokens; originals and citation offsets stay intact.
            tokens = sum(
                len(model.tokenizer(q, text, truncation=True, max_length=512)["input_ids"])
                for q, text in pairs
            )
            scores = model.predict(pairs, batch_size=8, show_progress_bar=False).tolist()
        if len(scores) != len(passages) or any(not math.isfinite(value) for value in scores):
            raise InvalidRerankResult("Reranker returned malformed scores")
        return RerankBatch(scores, tokens, (time.monotonic() - started) * 1000)


@lru_cache(maxsize=1)
def reranker():
    return LocalReranker(Settings().embedding_cache)
