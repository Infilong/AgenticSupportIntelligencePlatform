"""Embedding dispatch only after independent durable budget admission."""

import logging
import time
from uuid import UUID

from app.core.language import SupportedLanguage
from app.services.embedding_api import EmbeddingAPI
from app.services.embedding_attempts import EmbeddingAttemptLedger
from app.services.embedding_provider import EmbeddingProvider

logger = logging.getLogger(__name__)


class AccountedEmbeddingProvider(EmbeddingProvider):
    provider = "openai"

    def __init__(self, *, api: EmbeddingAPI, ledger: EmbeddingAttemptLedger,
                 workspace_id: UUID, language: SupportedLanguage,
                 token_cost_per_1k: float, purpose: str, graph_run_id: UUID | None = None):
        self.api = api
        self.ledger = ledger
        self.workspace_id = workspace_id
        self.language = language
        self.token_cost_per_1k = token_cost_per_1k
        self.purpose = purpose
        self.graph_run_id = graph_run_id
        self.model = api.model
        self.dimensions = api.dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            raise ValueError("Embedding input requires nonempty chunks")
        batches, batch, size = [], [], 0
        for text in texts:
            self.api.validate_inputs([text])
            length = len(text.encode("utf-8"))
            if batch and (len(batch) == 64 or size + length > 64_000):
                batches.append(batch)
                batch, size = [], 0
            batch.append(text)
            size += length
        batches.append(batch)
        return [vector for batch in batches for vector in self._embed_batch(batch)]

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        with self.ledger.execution(self.workspace_id) as owner:
            return self._owned_batch(texts, owner)

    def _owned_batch(self, texts, owner) -> list[list[float]]:
        self.api.validate_inputs(texts)
        attempt_id = self.ledger.begin(workspace_id=self.workspace_id, language=self.language,
            model=self.model, texts=texts, token_cost_per_1k=self.token_cost_per_1k,
            purpose=self.purpose, graph_run_id=self.graph_run_id, owner=owner)
        started = time.perf_counter()
        try:
            batch = self.api.embed(texts)
        except Exception:
            # Preserve the provider failure; pending usage survives a failed reconciliation write.
            try:
                self.ledger.finish(workspace_id=self.workspace_id, attempt_id=attempt_id,
                    owner=owner,
                    prompt_tokens=None, latency_ms=int((time.perf_counter() - started) * 1000))
            except Exception as accounting_error:
                logger.error("embedding_attempt_reconciliation_failed error_type=%s",
                             type(accounting_error).__name__)
            raise
        self.ledger.finish(workspace_id=self.workspace_id, attempt_id=attempt_id,
            owner=owner,
            prompt_tokens=batch.prompt_tokens,
            latency_ms=int((time.perf_counter() - started) * 1000))
        if batch.prompt_tokens > sum(len(text.encode("utf-8")) for text in texts):
            raise RuntimeError("Embedding usage exceeded admission estimate")
        return batch.vectors
