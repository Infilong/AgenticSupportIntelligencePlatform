"""Safe unexpected-error responses with the request's diagnostic reference."""

from starlette.requests import Request
from starlette.responses import JSONResponse


async def internal_error_response(request: Request, exc: Exception) -> JSONResponse:
    reference = getattr(request.state, "request_id", None)
    headers = {"Cache-Control": "no-store"}
    if reference is not None:
        headers["X-Request-ID"] = reference
    # ServerErrorMiddleware is outside the normal CORS layer. Reuse its configured allowlist.
    origin = request.headers.get("origin")
    allowed = request.app.state.cors_origins
    if origin and (origin in allowed or "*" in allowed):
        headers.update({
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Expose-Headers": "X-Request-ID",
            "Vary": "Origin",
        })
    return JSONResponse(status_code=500, headers=headers, content={"detail": {
        "code": "internal_error", "message": "An internal error occurred.",
        "request_id": reference,
    }})
