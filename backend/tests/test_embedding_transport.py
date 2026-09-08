import io
import json
import urllib.error

import pytest

from app.services.embedding_transport import (
    EmbeddingTransportError,
    OpenAIEmbeddingTransport,
    _NoRedirect,
)


def invoke():
    return OpenAIEmbeddingTransport().create(api_key="synthetic-key",
        model="text-embedding-3-small", dimensions=2, texts=["秘密"], timeout_seconds=9)


def test_request_contract_and_bounded_read(monkeypatch):
    seen = {}

    class Response(io.BytesIO):
        def read(self, size=-1):
            seen["read_limit"] = size
            return super().read(size)

    class Opener:
        def open(self, request, timeout):
            seen.update(request=request, timeout=timeout)
            return Response(b'{"data": []}')

    monkeypatch.setattr("urllib.request.build_opener", lambda *args: Opener())
    assert invoke() == {"data": []}
    request = seen["request"]
    assert request.full_url == "https://api.openai.com/v1/embeddings"
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer synthetic-key"
    assert json.loads(request.data) == {"model": "text-embedding-3-small", "dimensions": 2,
                                        "input": ["秘密"], "encoding_format": "float"}
    assert seen["timeout"] == 9
    assert seen["read_limit"] == 8_000_001


@pytest.mark.parametrize("error,code", [
    (urllib.error.HTTPError("https://secret", 429, "secret body", {}, io.BytesIO(b"secret")),
     "embedding_http_429"),
    (TimeoutError("secret"), "embedding_transport_TimeoutError"),
])
def test_transport_errors_do_not_expose_content(monkeypatch, error, code):
    class Opener:
        def open(self, request, timeout):
            raise error

    monkeypatch.setattr("urllib.request.build_opener", lambda *args: Opener())
    with pytest.raises(EmbeddingTransportError) as caught:
        invoke()
    assert str(caught.value) == code


@pytest.mark.parametrize("body", [b"x" * 8_000_001, b"invalid secret json", b"[]"],
                         ids=["oversized", "invalid-json", "unexpected-json-type"])
def test_invalid_or_oversized_body_is_rejected(monkeypatch, body):
    class Opener:
        def open(self, request, timeout):
            return io.BytesIO(body)

    monkeypatch.setattr("urllib.request.build_opener", lambda *args: Opener())
    with pytest.raises(EmbeddingTransportError) as caught:
        invoke()
    assert "secret" not in str(caught.value)


def test_redirects_cannot_forward_credentials_or_document_text():
    assert _NoRedirect().redirect_request(None, None, 307, "redirect", {},
                                           "https://elsewhere.invalid") is None
