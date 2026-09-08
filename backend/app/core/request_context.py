"""Request-local identity propagated into synchronous service workers."""

from contextvars import ContextVar

request_id_context: ContextVar[str | None] = ContextVar("asi_request_id", default=None)
