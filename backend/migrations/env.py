from alembic import context

from app.core.settings import Settings
from app.db.engine import make_engine


def run_migrations():
    engine = make_engine(Settings())
    try:
        with engine.connect() as connection:
            context.configure(connection=connection)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run_migrations()
