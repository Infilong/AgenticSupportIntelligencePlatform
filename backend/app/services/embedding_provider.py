from __future__ import annotations

import hashlib
import struct
from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    provider: str
    model: str
    dimensions: int

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class MockEmbeddingProvider(EmbeddingProvider):
    provider = "mock"
    model = "mock-multilingual-embedding-16"
    dimensions = 16

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for index in range(self.dimensions):
            start = (index * 2) % len(digest)
            raw = struct.unpack(">H", digest[start : start + 2])[0]
            values.append(round((raw / 65535.0) * 2 - 1, 6))
        return values
