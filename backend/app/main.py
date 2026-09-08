import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.health import router as health_router
from app.core.request_logging import RequestLogging
from app.core.settings import Settings
from app.db.engine import make_engine


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        app.state.settings = settings
        app.state.engine = make_engine(settings)
        try:
            yield
        finally:
            app.state.engine.dispose()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    app = FastAPI(title="Support Workbench", lifespan=lifespan)
    app.add_middleware(RequestLogging)
    app.include_router(health_router)
    return app
