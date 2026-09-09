import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.body_limit import BodyLimit
from app.core.health import router as health_router
from app.core.request_logging import RequestLogging
from app.core.settings import Settings
from app.db.engine import make_engine
from app.modules.conversations.routes import router as conversation_router
from app.modules.identity.routes import router as identity_router
from app.modules.knowledge.retrieval_routes import router as retrieval_router
from app.modules.knowledge.routes import router as knowledge_router
from app.modules.reviews.routes import router as review_router
from app.modules.support.routes import router as support_router
from app.modules.usage.routes import router as usage_router
from app.modules.workspaces.routes import router as workspace_router
from app.modules.workspaces.settings import router as settings_router


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
    app.add_middleware(BodyLimit)
    app.add_middleware(RequestLogging)
    app.include_router(health_router)
    app.include_router(identity_router)
    app.include_router(workspace_router)
    app.include_router(knowledge_router)
    app.include_router(retrieval_router)
    app.include_router(support_router)
    app.include_router(conversation_router)
    app.include_router(settings_router)
    app.include_router(usage_router)
    app.include_router(review_router)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, error):
        # Validation errors can contain password/body values; expose field names and types only.
        return JSONResponse(
            {"detail": [{"loc": item["loc"], "type": item["type"]} for item in error.errors()]},
            status_code=422,
        )

    return app
