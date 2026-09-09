"""Lightweight spawn entrypoint: retain startup phases before importing retrieval dependencies."""

import faulthandler
import time
from pathlib import Path


def killed_retrieval(url, workspace_id, actor_id, pipe, diagnostic_path):
    started = time.monotonic()

    def phase(name):
        pipe.send({"phase": name, "elapsed_seconds": time.monotonic() - started})

    with Path(diagnostic_path).open("w", encoding="utf-8") as output:
        faulthandler.dump_traceback_later(15, file=output)
        try:
            phase("launcher_started")
            from sqlalchemy import create_engine

            from app.modules.identity import models as identity_models  # noqa: F401
            from app.modules.knowledge.retrieval import retrieve

            phase("imports_ready")

            class Model:
                def encode_batch(self, texts, kind):
                    phase("inference_started")
                    pipe.recv()
                    raise AssertionError("Parent should terminate this process")

            engine = create_engine(url, hide_parameters=True)
            try:
                phase("engine_ready")
                retrieve(engine, workspace_id, actor_id, "synthetic crash test", provider=Model())
            finally:
                engine.dispose()
        finally:
            faulthandler.cancel_dump_traceback_later()
