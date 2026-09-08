from sqlalchemy import create_engine

from app.core.settings import Settings


def make_engine(settings: Settings):
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        pool_timeout=5,
        hide_parameters=True,
        connect_args={"connect_timeout": 3, "options": "-c statement_timeout=5000"},
    )
