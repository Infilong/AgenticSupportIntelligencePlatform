"""Bounded HTTP transport; callers own authorization, admission and durable accounting."""

import json
import urllib.error
import urllib.request
from typing import Any, Protocol


class EmbeddingTransportError(RuntimeError):
    """Sanitized transport failure; usage may be unknown after dispatch."""


class EmbeddingTransport(Protocol):
    def create(self, *, api_key: str, model: str, dimensions: int,
               texts: list[str], timeout_seconds: int) -> dict[str, Any]: ...


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class OpenAIEmbeddingTransport:
    def create(self, *, api_key: str, model: str, dimensions: int,
               texts: list[str], timeout_seconds: int) -> dict[str, Any]:
        request = urllib.request.Request(
            "https://api.openai.com/v1/embeddings",
            data=json.dumps({"input": texts, "model": model, "dimensions": dimensions,
                             "encoding_format": "float"}).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        # Do not forward credentials or protected text through provider redirects.
        opener = urllib.request.build_opener(_NoRedirect())
        try:
            with opener.open(request, timeout=timeout_seconds) as response:
                raw = response.read(8_000_001)
            if len(raw) > 8_000_000:
                raise EmbeddingTransportError("embedding_response_too_large")
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise EmbeddingTransportError("embedding_response_invalid_json_object")
            return value
        except urllib.error.HTTPError as exc:
            # Never retain response bodies, headers, URLs or exception strings in public errors.
            code = exc.code
            exc.close()
            raise EmbeddingTransportError(f"embedding_http_{code}") from None
        except (OSError, ValueError) as exc:
            raise EmbeddingTransportError(f"embedding_transport_{type(exc).__name__}") from None
