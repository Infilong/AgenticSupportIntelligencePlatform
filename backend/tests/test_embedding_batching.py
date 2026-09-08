from contextlib import nullcontext
from uuid import uuid4

import pytest

from app.core.language import SupportedLanguage
from app.services.accounted_embeddings import AccountedEmbeddingProvider
from app.services.embedding_api import EmbeddingAPI


class Ledger:
    def __init__(self):
        self.attempts = []

    def begin(self, **kwargs):
        self.attempts.append(kwargs)
        return uuid4()

    def execution(self, workspace_id):
        return nullcontext(None)

    def finish(self, **kwargs):
        pass


class Transport:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        texts = kwargs["texts"]
        self.calls.append(texts)
        return {"model": kwargs["model"],
            "usage": {"prompt_tokens": len(texts), "total_tokens": len(texts)},
            "data": [{"index": index, "embedding": [0.5]} for index in range(len(texts))]}


def provider():
    transport, ledger = Transport(), Ledger()
    api = EmbeddingAPI(api_key="synthetic", model="text-embedding-3-small", dimensions=1,
                       transport=transport)
    return AccountedEmbeddingProvider(api=api, ledger=ledger, workspace_id=uuid4(),
        language=SupportedLanguage.en, purpose="embedding_document", token_cost_per_1k=0.001)


@pytest.mark.parametrize("texts,counts", [(["word"] * 65, [64, 1]),
                                         (["x" * 8000] * 17, [8, 8, 1])])
def test_batches_by_count_and_bytes_and_accounts_for_each_request(texts, counts):
    configured = provider()
    vectors = configured.embed_texts(texts)
    assert len(vectors) == len(texts)
    assert [len(batch) for batch in configured.api.transport.calls] == counts
    assert len(configured.ledger.attempts) == len(counts)
    assert [text for batch in configured.api.transport.calls for text in batch] == texts


def test_invalid_late_chunk_prevents_any_dispatch_or_admission():
    configured = provider()
    with pytest.raises(ValueError):
        configured.embed_texts(["valid"] * 65 + ["x" * 8001])
    assert configured.api.transport.calls == []
    assert configured.ledger.attempts == []
