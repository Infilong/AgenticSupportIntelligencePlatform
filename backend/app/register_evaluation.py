"""Register a completed local v1 retrieval comparison, without executing AI or changing defaults."""

import argparse
import json
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.db.engine import make_engine
from app.modules.evaluations.service import register


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--actor-id", type=UUID, required=True)
    args = parser.parse_args()
    # Bounded read before JSON decoding; no raw report or input errors in logs.
    with args.report.open("rb") as source:
        raw = source.read(8 * 1024 * 1024 + 1)
    engine = make_engine(Settings())
    try:
        with Session(engine) as db, db.begin():
            record = register(db, raw, args.actor_id)
            result = {
                "id": str(record.id),
                "workspace_id": str(record.workspace_id),
                "report_sha256": record.report_sha256,
            }
        print(json.dumps(result))
    except (ValueError, HTTPException):
        print(
            "Registration rejected: require a complete v1 report and primary-workspace administrator; "
            "all traces must match its stored requests."
        )
        return 1
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
