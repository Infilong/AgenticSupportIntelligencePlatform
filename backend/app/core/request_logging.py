"""Structured HTTP outcome logs without request bodies, queries or resource IDs."""

import json
import logging
import time
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.request_context import request_id_context


def request_logger(name: str = "asi.http") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


class RequestLogMiddleware:
    def __init__(self, app: ASGIApp, logger: logging.Logger | None = None):
        self.app = app
        self.logger = logger if logger is not None else request_logger()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = str(uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        started = time.perf_counter()
        status = 500
        error_type = None

        async def send_with_id(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                headers = [
                    (name, value) for name, value in message.get("headers", [])
                    if name.lower() != b"x-request-id"
                ]
                message = {**message, "headers": [*headers, (b"x-request-id", request_id.encode())]}
            await send(message)

        token = request_id_context.set(request_id)
        try:
            await self.app(scope, receive, send_with_id)
        except Exception as exc:
            error_type = type(exc).__name__
            raise
        finally:
            request_id_context.reset(token)
            route = getattr(scope.get("route"), "path", "<unmatched>")
            self.logger.info(json.dumps({
                "event": "http_request",
                "request_id": request_id,
                "method": scope["method"],
                "route": route,
                "status": status,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "error_type": error_type,
            }, sort_keys=True))
