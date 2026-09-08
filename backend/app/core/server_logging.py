"""Content-free exception diagnostics for the server logger."""

import copy
import json
import logging
from pathlib import Path
from traceback import walk_tb


class ServerFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        safe = copy.copy(record)
        safe.exc_text = None
        if safe.exc_info:
            safe.msg = "Unhandled server exception"
            safe.args = ()
            safe.stack_info = None
        return super().format(safe)

    def formatException(self, exc_info) -> str:
        pending = [exc_info[1]]
        seen = set()
        exceptions = []
        while pending and len(exceptions) < 8:
            error = pending.pop(0)
            if error is None or id(error) in seen:
                continue
            seen.add(id(error))
            frames = [{"file": Path(frame.f_code.co_filename).name,
                       "function": frame.f_code.co_name, "line": line}
                      for frame, line in walk_tb(error.__traceback__)]
            exceptions.append({"type": type(error).__name__, "frames": frames[-20:]})
            if isinstance(error, BaseExceptionGroup):
                pending.extend(error.exceptions[:8])
            pending.append(error.__cause__ or (
                None if error.__suppress_context__ else error.__context__
            ))
        return json.dumps({"event": "server_exception", "exceptions": exceptions}, sort_keys=True)
