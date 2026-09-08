"""Generate the public API contract without connecting to any database."""

import json
import sys

from app.core.settings import Settings
from app.main import create_app

if __name__ == "__main__":
    app = create_app(Settings(database_url="postgresql+psycopg://unused:unused@localhost/unused"))
    sys.stdout.write(json.dumps(app.openapi()))
