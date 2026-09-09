"""Versioned development transport. Replaying a contribution is not model inference."""

import json
from copy import deepcopy

from fastapi import HTTPException
from langchain_core.runnables import RunnableLambda

from app.modules.support.context import digest

VERSION = "development-request-v1"


def render(context):
    """Keep this renderer stable: existing request identities must survive code upgrades."""
    payload = {key: context[key] for key in ("original", "language", "sources")}
    return {
        "schema_version": VERSION,
        "context_hash": digest(context),
        "prompt_version": context["prompt_version"],
        "messages": [
            {"role": "system", "content": context["instruction"]},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False, sort_keys=True)},
        ],
    }


def request_for(handoff):
    """Legacy rows are reconstructed, never represented as previously recorded messages."""
    expected = render(handoff.context)
    if expected["context_hash"] != handoff.context_hash or (
        handoff.prompt_version != handoff.context["prompt_version"]
    ):
        raise HTTPException(409, "Development evidence identity changed; start a fresh attempt")
    stored = handoff.generation_request
    if stored is None and handoff.request_hash is None:
        return expected, digest(expected), "reconstructed"
    if stored != expected or handoff.request_hash != digest(expected):
        raise HTTPException(409, "Development request identity changed; start a fresh attempt")
    return deepcopy(stored), handoff.request_hash, "recorded"


def snapshot(handoff):
    request, request_hash, _ = request_for(handoff)
    if handoff.response is None or handoff.contributor_id is None:
        raise HTTPException(409, "An attributed development response is required")
    response = deepcopy(handoff.response)
    identity = digest({"contributor": str(handoff.contributor_id), "response": response})
    if identity != handoff.response_hash or response.get("context_hash") != handoff.context_hash:
        raise HTTPException(409, "Development response identity changed; start a fresh attempt")
    if response.get("request_hash") not in (None, request_hash):
        raise HTTPException(409, "Development response belongs to a different request")
    return {"request": request, "request_hash": request_hash, "response": response}


def _consume(record):
    # No lookup into eval fixtures, network call, callbacks or inferred usage measurements.
    if digest(record["request"]) != record["request_hash"]:
        raise ValueError("Development request changed during replay")
    return deepcopy(record["response"])


replay = RunnableLambda(_consume, name="attributed_development_replay")
