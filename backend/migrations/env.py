from alembic import context
from sqlalchemy import text

from app.core.settings import Settings
from app.db.engine import make_engine


def run_migrations():
    supplied = context.config.attributes.get("connection")
    if supplied is not None:
        migrate(supplied)
        return
    engine = make_engine(Settings())
    try:
        with engine.begin() as connection:
            migrate(connection)
    finally:
        engine.dispose()


def migrate(connection):
    schema = connection.scalar(text("SELECT current_schema()"))
    context.configure(connection=connection, version_table_schema=schema)
    with context.begin_transaction():
        context.run_migrations()


run_migrations()
