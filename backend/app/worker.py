"""Run with python -m app.worker after database migration."""

import logging
import time

from app.db.session import engine
from app.services.task_worker import work_once

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO)
    if engine.dialect.name != "postgresql":
        raise RuntimeError("The task worker requires PostgreSQL")
    while True:
        try:
            if not work_once(engine):
                time.sleep(0.5)
        except KeyboardInterrupt:
            return
        except Exception as error:
            logger.error("task_worker_error error_type=%s", type(error).__name__)
            time.sleep(1)


if __name__ == "__main__":
    main()
