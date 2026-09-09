# Standalone local database backup

## Execution brief

RESTORE/operations: expose the planned backup entry point without creating a restoration clone.
Normal bounded tooling slice, root sole implementation owner. Read root, scripts, infrastructure,
backend and docs guides. Reuse the already verified exported-snapshot dump/fingerprint code in
restore_drill.py, with an explicit backup-only mode and an early return before any database write.
Keep the default restore drill unchanged. No cloud, retention daemon, deletion, schema or UI work.

Add manage.py backup, timestamped backup evidence and explicit restoration-unverified reporting.
Source remains the isolated development asi-rebuild-v1 database, not the packaged release or
archive. Dumps contain application data/authentication records; configuration and model caches
are outside scope. A successful export is not recovery proof. Retain failures and partial files.

Verify mode isolation and failed/empty dumps with focused unit tests, real PostgreSQL export,
hash/size/archive listing and unchanged database inventory, then run the default restoration
drill regression. Independent safety review, updated owning docs/generated references/semantic
receipts, preparation checks and a small branch commit/push close this slice. Stop at14:58 UTC.

## Design review

Independent read-only review supports reusing the export boundary, provided backup reports omit
clone/parity claims, return before createdb/restore/exercise, failures exit nonzero, and console
output identifies backup evidence accurately. Sequence metadata is observational because
PostgreSQL sequences are not MVCC-snapshot data; do not imply atomic sequence parity.

## Initial verification

First direct unit invocation failed all four setups because the shared Windows pytest temp
directory is inaccessible. No test body ran. A new repository-local basetemp avoids that
unrelated ACL without changing it. Review also found an unconfigured synthetic snapshot value;
the fixture now returns a serializable snapshot string. Four focused tests then pass in0.78s.
No production boundary change was required by that review. Real export/recovery checks follow.

## Runtime evidence

Real `backup` passes at `.artifacts/m6/backup-20260909T135747Z`, wrapper
`.artifacts/m0/backup-20260909T135746242474Z`. The archive is4,093,256 bytes; a separate SHA-256
check and PostgreSQL archive listing pass. It fingerprints23 public tables. Exact database
inventory before/after is unchanged. Independent evidence is retained under
`.artifacts/m6/backup-verification-20260909`; no database restore was attempted by this command.

The default fresh-snapshot restoration regression passes at
`.artifacts/m6/restore-20260909T135902Z`, wrapper `.artifacts/m0/restore-20260909T135901369847Z`.
All23 public tables and metadata match the snapshot. New disposable clone
`asi_restore_21682d1240de` processes run `d78441e4-1664-4f98-8fdb-d87bb7e9c5a0` to clarification,
with a succeeded job,3 checkpoints and zero model calls. No inherited active jobs existed.
This drill made its own fresh snapshot; it did not consume the preceding standalone archive.

All69 backend unit tests pass at `.artifacts/m0/backend-20260909T135808912077Z`, retaining the
existing AnyIO deprecation warning. Focused test Ruff and changed-script F checks pass.
Workbench checkpointfb2db23's hosted CI34360000750 passed before this backup checkpoint.

Independent safety and semantic-documentation reviews closed with no remaining findings.
All46 preparation checks pass at .artifacts/m0/prep-20260909T140141366470Z. This completion
note follows verification and does not alter runtime or mapped documentation contracts.
