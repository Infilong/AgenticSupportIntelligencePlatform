"""Read a bounded five-session workload snapshot; never mutate or infer provider execution."""

import argparse
import json
from uuid import UUID

from sqlalchemy import text

from app.core.settings import Settings
from app.db.engine import make_engine


def profile(connection, workspace_id, run_ids, document_ids):
    if len(set(run_ids)) != 5 or len(run_ids) != 5 or len(set(document_ids)) != 2 or len(document_ids) != 2:
        raise ValueError("Require five distinct runs and two documents")
    connection.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
    connection.execute(text("SET LOCAL statement_timeout = '5s'"))
    params = {"workspace": workspace_id, "runs": run_ids, "documents": document_ids}
    runs = (
        connection.execute(
            text("""
        SELECT r.id, r.created_at, min(h.created_at) AS handoff_created_at,
               r.job_id, r.retrieval_id, r.state, r.outcome, j.state AS job_state,
               j.attempts, count(s.id) AS recorded_steps,
               (extract(epoch FROM (min(s.created_at) - j.created_at))*1000)::double precision
                   AS admission_to_first_node_ms,
               (extract(epoch FROM (min(h.created_at) - j.created_at))*1000)::double precision
                   AS admission_to_handoff_ms
        FROM support_runs r JOIN jobs j ON j.workspace_id=r.workspace_id AND j.id=r.job_id
        LEFT JOIN support_steps s ON s.workspace_id=r.workspace_id AND s.run_id=r.id
        LEFT JOIN development_handoffs h ON h.workspace_id=r.workspace_id AND h.run_id=r.id
        WHERE r.workspace_id=:workspace AND r.id=ANY(:runs)
        GROUP BY r.id,j.id ORDER BY r.id
    """),
            params,
        )
        .mappings()
        .all()
    )
    documents = (
        connection.execute(
            text("""
        SELECT d.id, v.id AS version_id, v.created_at, v.indexed_at,
               v.job_id, v.checksum, octet_length(v.original) AS bytes,
               j.state AS job_state, j.attempts,
               (extract(epoch FROM (v.indexed_at - v.created_at))*1000)::double precision
                   AS admission_to_indexed_ms
        FROM documents d JOIN document_versions v
          ON v.workspace_id=d.workspace_id AND v.id=d.active_version_id
        JOIN jobs j ON j.workspace_id=v.workspace_id AND j.id=v.job_id
        WHERE d.workspace_id=:workspace AND d.id=ANY(:documents) AND NOT d.withdrawn
        ORDER BY d.id
    """),
            params,
        )
        .mappings()
        .all()
    )
    if len(runs) != 5 or len(documents) != 2:
        raise ValueError("Requested runs or ready documents are unavailable in this workspace")
    corpus = (
        connection.execute(
            text("""
        SELECT count(*) AS active_documents, coalesce(sum(octet_length(v.original)),0) AS bytes,
          (SELECT count(*) FROM document_chunks c JOIN documents active
             ON active.workspace_id=c.workspace_id AND active.active_version_id=c.version_id
             WHERE c.workspace_id=:workspace AND NOT active.withdrawn) AS active_chunks
        FROM documents d JOIN document_versions v
          ON v.workspace_id=d.workspace_id AND v.id=d.active_version_id
        WHERE d.workspace_id=:workspace AND NOT d.withdrawn
    """),
            params,
        )
        .mappings()
        .one()
    )
    background = next(row for row in documents if row["id"] == document_ids[1])
    ends = [row["handoff_created_at"] for row in runs]
    overlap = None
    if (
        all(ends)
        and all(row["handoff_created_at"] >= row["created_at"] for row in runs)
        and (background["indexed_at"] is not None and background["indexed_at"] >= background["created_at"])
    ):
        overlap = background["created_at"] < max(ends) and background["indexed_at"] > min(
            row["created_at"] for row in runs
        )
    return {
        "workspace_id": str(workspace_id),
        "runs": [dict(row) for row in runs],
        "documents": [dict(row) for row in documents],
        "current_corpus": dict(corpus),
        "admitted_ingestion_window_overlaps_support_window": overlap,
        "timing_note": "Admission-to-first-node includes queue wait and pre-node work. "
        "Admission-to-indexed includes queue wait. Null is unmeasured; "
        "negative timestamps indicate a clock anomaly, not zero elapsed time.",
        "overlap_note": "The second document's admission-to-indexed interval is compared with "
        "the five requests' admission-to-handoff interval. This includes queued work; "
        "it is not evidence of simultaneous model inference. Null means missing/anomalous timestamps.",
        "generation": "not_exercised",
        "quality": "not_measured",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-id", type=UUID, required=True)
    parser.add_argument("--run-ids", type=UUID, nargs=5, required=True)
    parser.add_argument("--document-ids", type=UUID, nargs=2, required=True)
    args = parser.parse_args()
    engine = make_engine(Settings())
    try:
        with engine.connect() as connection, connection.begin():
            result = profile(connection, args.workspace_id, args.run_ids, args.document_ids)
        print(json.dumps(result, default=str))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
