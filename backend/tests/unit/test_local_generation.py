import json

import pytest
from langchain_core.messages import AIMessage
from pydantic import ValidationError

from app.core.settings import GenerationSettings
from app.providers import local_generation as provider


@pytest.mark.parametrize(
    "language,name", [("en", "English"), ("ja", "Japanese"), ("zh", "Simplified Chinese")]
)
def test_requested_language_and_server_owned_citations(monkeypatch, language, name):
    context = {
        "original": "question",
        "language": language,
        "sources": [{"title": "policy", "text": "Real policy text.", "chunk_id": "source-1"}],
    }

    class Model:
        def __init__(self, **kwargs):
            assert kwargs["client_kwargs"]["follow_redirects"] is False
            assert kwargs["format"] == "json"

        def invoke(self, messages):
            assert name in messages[0]["content"]
            return AIMessage(content=json.dumps({"answer": "A draft", "source_ids": [1]}))

    monkeypatch.setattr(provider, "ChatOllama", Model)
    result, usage = provider.generate(
        provider.request_for(context, "model", "http://localhost:11434"), context
    )
    assert result["citations"] == [{"chunk_id": "source-1", "quote": "Real policy text."}]
    assert result["review_category"] == "unclassified"  # Model cannot grant operator approval.
    assert usage == {}


@pytest.mark.parametrize("ids", [[0], [2], [1, 1]])
def test_invalid_source_selection_rejected(monkeypatch, ids):
    class Model:
        def __init__(self, **kwargs):
            pass

        def invoke(self, messages):
            return AIMessage(content=json.dumps({"answer": "A draft", "source_ids": ids}))

    monkeypatch.setattr(provider, "ChatOllama", Model)
    with pytest.raises(ValueError, match="source"):
        provider.generate(
            {"model": "test", "endpoint": "http://localhost:11434", "messages": []},
            {"sources": [{"text": "policy", "chunk_id": "1"}]},
        )


@pytest.mark.parametrize(
    "url", ["https://api.example.com", "http://user@localhost:11434", "http://localhost/api"]
)
def test_remote_or_credentialed_endpoint_rejected(url):
    with pytest.raises(ValidationError):
        GenerationSettings(ollama_url=url)


def test_no_relevant_sources_is_a_valid_model_outcome(monkeypatch):
    class Model:
        def __init__(self, **kwargs):
            pass

        def invoke(self, messages):
            return AIMessage(content='{"answer":"Please specify which policy you need.","source_ids":[]}')

    monkeypatch.setattr(provider, "ChatOllama", Model)
    response, _ = provider.generate(
        {"model": "test", "endpoint": "http://localhost:11434", "messages": []}, {"sources": []}
    )
    assert response["citations"] == []
