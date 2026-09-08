from copy import deepcopy

import pytest

from app.services.embedding_api import EmbeddingAPI, EmbeddingResponseError
from app.services.embedding_transport import EmbeddingTransportError


class StubTransport:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return deepcopy(self.payload)


def response():
    return {"model": "text-embedding-3-small",
            "usage": {"prompt_tokens": 12, "total_tokens": 12},
            "data": [{"index": 1, "embedding": [0.5, 0.25]},
                     {"index": 0, "embedding": [0.25, 0.5]}]}


def api(transport):
    return EmbeddingAPI(api_key="test-key", model="text-embedding-3-small", dimensions=2,
                        transport=transport)


def test_restores_input_order_and_returns_usage():
    stub = StubTransport(response())
    batch = api(stub).embed(["返金条件", "退款条件"])
    assert batch.vectors == [[0.25, 0.5], [0.5, 0.25]]
    assert batch.prompt_tokens == 12
    assert batch.model == "text-embedding-3-small"
    assert stub.calls[0]["texts"] == ["返金条件", "退款条件"]
    assert stub.calls[0]["timeout_seconds"] == 30


@pytest.mark.parametrize("texts", [[], [""], [" "], ["x"] * 65, ["文" * 2667],
                                   ["x" * 8000] * 9, [None]])
def test_bad_inputs_never_dispatch(texts):
    stub = StubTransport()
    with pytest.raises(ValueError, match="Embedding"):
        api(stub).embed(texts)
    assert stub.calls == []


@pytest.mark.parametrize("field,value", [
    ("model", "different-model"), ("usage", None),
    ("usage", {"prompt_tokens": True, "total_tokens": 1}),
    ("usage", {"prompt_tokens": 1, "total_tokens": 2}),
    ("usage", {"prompt_tokens": -1, "total_tokens": -1}),
    ("data", []), ("data", [{"index": 0, "embedding": [0.2, 0.3]}] * 2),
])
def test_rejects_incomplete_or_incompatible_responses(field, value):
    payload = response()
    payload[field] = value
    with pytest.raises(EmbeddingResponseError):
        api(StubTransport(payload)).embed(["English", "中文"])


@pytest.mark.parametrize("vector", [[0.0, 0.0], [float("nan"), 0.5], [float("inf"), 0],
                                    [True, 0.5], ["secret", 0], [0.2], [2.0, 0.5]])
def test_rejects_invalid_vectors_without_echoing_payload(vector):
    payload = response()
    payload["data"][0]["embedding"] = vector
    with pytest.raises(EmbeddingResponseError, match="vector is invalid") as caught:
        api(StubTransport(payload)).embed(["English", "中文"])
    assert "secret" not in str(caught.value)


def test_failure_is_not_retried_or_replaced_with_mock_vectors():
    stub = StubTransport(error=EmbeddingTransportError("embedding_http_429"))
    with pytest.raises(EmbeddingTransportError, match="429"):
        api(stub).embed(["policy"])
    assert len(stub.calls) == 1
