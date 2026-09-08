from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from app.core.settings import Settings


def make_engine(settings: Settings):
    url = make_url(settings.database_url.get_secret_value())
    options = url.query.get("options", "")
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        pool_timeout=5,
        hide_parameters=True,
        connect_args={"connect_timeout": 3, "options": f"{options} -c statement_timeout=5000"},
    )
