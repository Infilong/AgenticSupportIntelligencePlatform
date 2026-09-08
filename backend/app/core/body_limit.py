from fastapi.responses import JSONResponse


class BodyLimit:
    """Bound multipart parsing too, including requests without a Content-Length header."""

    def __init__(self, app, limit=6 * 1024 * 1024):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > self.limit:
                return await JSONResponse(
                    {"detail": "Request exceeds the 6 MiB upload limit"}, status_code=413
                )(scope, receive, send)
            if not message.get("more_body", False):
                break
        sent = False

        async def bounded_receive():
            nonlocal sent
            if sent:
                return await receive()
            sent = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, bounded_receive, send)
