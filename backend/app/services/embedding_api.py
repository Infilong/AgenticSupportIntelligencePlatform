"""Validated embedding API boundary. Runtime callers must account for every attempt."""

import math
from dataclasses import dataclass

from app.services.embedding_transport import EmbeddingTransport, OpenAIEmbeddingTransport


class EmbeddingResponseError(ValueError):
    """The provider returned unusable output; usage must be reconciled by the caller."""


@dataclass(frozen=True)
class EmbeddingBatch:
    vectors: list[list[float]]
    prompt_tokens: int
    model: str


class EmbeddingAPI:
    """One bounded request, no automatic retries and no implicit mock fallback."""

    def __init__(self, *, api_key: str, model: str, dimensions: int,
                 timeout_seconds: int = 30, transport: EmbeddingTransport | None = None):
        limits = {"text-embedding-3-small": 1536, "text-embedding-3-large": 3072}
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("Embedding API key is required")
        if model not in limits:
            raise ValueError("Unsupported embedding model")
        if type(dimensions) is not int or not 1 <= dimensions <= limits[model]:
            raise ValueError("Invalid embedding dimensions")
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 120:
            raise ValueError("Embedding timeout must be between 1 and 120 seconds")
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions
        self.timeout_seconds = timeout_seconds
        self.transport = transport or OpenAIEmbeddingTransport()

    @staticmethod
    def validate_inputs(texts: list[str]) -> None:
        # Conservative UTF-8 byte caps bound token input without heuristic undercounting.
        # Callers batch already-chunked documents; this API never accepts a raw long document.
        if not isinstance(texts, list) or not 1 <= len(texts) <= 64:
            raise ValueError("Embedding input requires 1 to 64 chunks")
        if any(not isinstance(item, str) or not item.strip()
               or len(item.encode("utf-8")) > 8000 for item in texts):
            raise ValueError("Embedding chunks must be nonempty and at most 8000 UTF-8 bytes")
        if sum(len(item.encode("utf-8")) for item in texts) > 64_000:
            raise ValueError("Embedding batch exceeds 64000 UTF-8 bytes")

    def embed(self, texts: list[str]) -> EmbeddingBatch:
        self.validate_inputs(texts)
        payload = self.transport.create(api_key=self.api_key, model=self.model,
                                        dimensions=self.dimensions, texts=texts,
                                        timeout_seconds=self.timeout_seconds)
        return self._parse(payload, len(texts))

    def _parse(self, payload: dict, count: int) -> EmbeddingBatch:
        if not isinstance(payload, dict) or payload.get("model") != self.model:
            raise EmbeddingResponseError("Embedding response model mismatch")
        usage = payload.get("usage")
        if (not isinstance(usage, dict) or type(usage.get("prompt_tokens")) is not int
                or usage["prompt_tokens"] < 1
                or type(usage.get("total_tokens")) is not int
                or usage["total_tokens"] != usage["prompt_tokens"]):
            raise EmbeddingResponseError("Embedding response usage is missing or invalid")
        data = payload.get("data")
        if not isinstance(data, list) or len(data) != count:
            raise EmbeddingResponseError("Embedding response vector count mismatch")
        indexed = {}
        for item in data:
            if not isinstance(item, dict):
                raise EmbeddingResponseError("Embedding response entry is invalid")
            index, vector = item.get("index"), item.get("embedding")
            if type(index) is not int or not 0 <= index < count or index in indexed:
                raise EmbeddingResponseError("Embedding response index is invalid")
            if (not isinstance(vector, list) or len(vector) != self.dimensions
                    or any(type(value) not in (int, float) or not math.isfinite(value)
                           or abs(value) > 1 for value in vector)
                    or not any(vector)):
                raise EmbeddingResponseError("Embedding response vector is invalid")
            indexed[index] = [float(value) for value in vector]
        return EmbeddingBatch([indexed[index] for index in range(count)],
                              usage["prompt_tokens"], self.model)
