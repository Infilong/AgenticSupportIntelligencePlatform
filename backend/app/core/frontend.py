"""Optional built UI: fixed navigation routes and a dedicated public assets directory."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles


class BuiltAssets(StaticFiles):
    async def get_response(self, path, scope):
        if any(part.startswith(".") for part in Path(path).parts):
            raise HTTPException(404, "Not found")
        response = await super().get_response(path, scope)
        if response.status_code in {200, 304}:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            response.headers["X-Content-Type-Options"] = "nosniff"
        return response


def install_frontend(app: FastAPI, directory: Path) -> None:
    root = directory.resolve(strict=True)
    index = (root / "index.html").resolve(strict=True)
    assets = (root / "assets").resolve(strict=True)
    if not index.is_file() or not assets.is_dir() or index.parent != root or assets.parent != root:
        raise ValueError("Built frontend requires index.html and assets inside its static directory")

    def shell():
        return FileResponse(index, headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

    # API routes are registered first. Missing API/assets/private paths never fall back to HTML.
    app.mount("/assets", BuiltAssets(directory=assets, follow_symlink=False), name="built-assets")
    base = "/w/{workspace_id:uuid}"
    routes = [
        "/",
        base,
        f"{base}/messages/{{message_id:uuid}}",
        f"{base}/runs/{{run_id:uuid}}",
        f"{base}/knowledge",
        f"{base}/knowledge/search",
        f"{base}/knowledge/{{document_id:uuid}}",
        f"{base}/settings",
        f"{base}/quality",
        f"{base}/members",
    ]
    for path in routes:
        app.add_api_route(path, shell, methods=["GET", "HEAD"], include_in_schema=False)
