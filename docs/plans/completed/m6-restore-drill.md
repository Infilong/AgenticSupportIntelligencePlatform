# Isolated restoration proof

Outcome RESTORE: a fresh source snapshot restores without loss and the restored application can
handle a new request. Root owns scripts/restore_drill.py and its dispatcher/docs; read scripts,
infra and backend guides. No product feature or RAG tuning; no paid calls or external actions.

Verify the existing rebuild container identity, export a read-only repeatable-read snapshot,
hash/count every public table in that snapshot and pg_dump the same exported snapshot. Restore
only to a fresh random asi_restore_<hex> database; createdb must fail if already present. No
overwrite/drop operation. Compare fingerprints before any login/worker mutation. Then quiesce
inherited active jobs only in the disposable clone and exercise a new isolated user/workspace
through real login→message→worker/LangGraph→clarification. Never start the ordinary infinite
worker against restored inherited jobs. Retain the dump, clone and report for review.

This proves snapshot parity and a new deterministic processing flow, not external API generation,
restored RAG quality, earlier backup age/recovery-point objectives or complete release readiness.
Record failures and exact limits. Independent safety review and an actual drill are required.

## Verification checkpoint — 2026-09-09

Drill passed at `.artifacts/m6/restore-20260909T095111Z/report.json`; command/source evidence is
`.artifacts/m0/restore-20260909T095110422764Z`. All 22 public tables and extension versions match
the exported snapshot; no public sequences exist. The retained disposable database is
`asi_restore_e7f3e3c21909`. A new authenticated message completed as clarification_needed,
with a succeeded job, three graph checkpoints and zero model calls. No inherited active jobs
were present. This uses ASGI TestClient and in-process worker execution, not restored network
services or a browser. The ordinary app remains connected to its original database.

Independent safety review identified missing command/query deadlines and incomplete sequence
metadata. Both were fixed before the successful drill; sequence checks now include is_called.
Final independent evidence and documentation reviews passed. All 45 preparation checks passed
at `.artifacts/m0/prep-20260909T095644938452Z`; implementation committed/pushed as ece351d.
No inherited active jobs existed, so quarantine behavior was not exercised. Forced-timeout
cleanup was not demonstrated by the successful drill. These remain limits, not passing claims.
