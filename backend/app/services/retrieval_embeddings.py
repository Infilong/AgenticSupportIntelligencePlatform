"""Query embedding validation, separate from retrieval persistence and ranking."""

import math
from uuid import UUID


class RetrievalError(ValueError):
    def __init__(self, message: str, *, trace_id: UUID | None = None):
        super().__init__(message)
        self.trace_id = trace_id


def validate_embedding(vector: list[float], dimensions: int) -> None:
    if (not isinstance(vector, list) or len(vector) != dimensions
            or any(isinstance(value, bool) or not isinstance(value, (int, float))
                   or not math.isfinite(value) for value in vector)
            or not any(vector)):
        raise RetrievalError(
            "Invalid embedding: expected a finite, nonzero vector of configured dimensions")


def embed_query(provider, query: str, stored_vectors: list[list[float]]) -> list[float]:
    for vector in stored_vectors:
        validate_embedding(vector, provider.dimensions)
    vectors = provider.embed_texts([query])
    if not isinstance(vectors, list) or len(vectors) != 1:
        raise RetrievalError("Query embedding response must contain exactly one vector")
    validate_embedding(vectors[0], provider.dimensions)
    return vectors[0]
