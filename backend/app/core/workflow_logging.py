"""Content-free links from an HTTP request to a persisted graph run."""

import json
from uuid import UUID

from app.core.request_context import request_id_context
from app.core.request_logging import request_logger


def log_graph_created(graph_run_id: UUID, trace_id: str | None) -> None:
    request_id = request_id_context.get()
    if request_id is None:
        return
    request_logger("asi.workflow").info(json.dumps({
        "event": "graph_run_created",
        "request_id": request_id,
        "graph_run_id": str(graph_run_id),
        "trace_id": trace_id,
    }, sort_keys=True))
