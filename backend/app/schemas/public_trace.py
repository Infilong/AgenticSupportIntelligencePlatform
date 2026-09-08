"""Redact the final serialized response, including nested model-copy updates."""

from pydantic import BaseModel, model_serializer

from app.core.trace_redaction import redact_trace


class PublicTraceResponse(BaseModel):
    @model_serializer(mode="wrap")
    def redact_response(self, handler):
        return redact_trace(handler(self))
