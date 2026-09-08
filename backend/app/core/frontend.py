"""Expose only the compiled browser entry point and its asset directory."""

from pathlib import Path

from fastapi import FastAPI
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles


def mount_frontend(app: FastAPI, directory: str | None) -> None:
    if directory is None:
        return
    root = Path(directory).resolve()
    index = root / "index.html"
    assets = root / "assets"
    if not index.is_file() or not assets.is_dir():
        raise ValueError("FRONTEND_DIST_PATH must contain index.html and an assets directory")

    @app.get("/", include_in_schema=False)
    def browser_index() -> FileResponse:
        return FileResponse(index, media_type="text/html", headers={
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
        })

    app.mount("/assets", StaticFiles(directory=assets, follow_symlink=False), name="browser-assets")
