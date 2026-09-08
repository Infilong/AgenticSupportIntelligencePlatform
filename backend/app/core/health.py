from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/api/health", tags=["health"])
ROOT = Path(__file__).resolve().parents[2]


def expected_revision():
    config = Config()
    config.set_main_option("script_location", str(ROOT / "migrations"))
    return ScriptDirectory.from_config(config).get_current_head()


@router.get("/live")
def live():
    return {"status": "alive"}


@router.get("/ready")
def ready(request: Request):
    try:
        with request.app.state.engine.connect() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            vector = connection.execute(text("SELECT extversion FROM pg_extension WHERE extname='vector'"))
            if revision != expected_revision() or vector.scalar_one_or_none() is None:
                return JSONResponse({"status": "not_ready", "reason": "migration_required"}, status_code=503)
    except SQLAlchemyError:
        return JSONResponse({"status": "not_ready", "reason": "database_unavailable"}, status_code=503)
    return {"status": "ready", "provider_mode": request.app.state.settings.provider_mode}
