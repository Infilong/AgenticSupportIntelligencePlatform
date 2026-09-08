# Database and migration guide

SQLAlchemy entities live in [models](../app/models/); session construction lives in
[db/session.py](../app/db/session.py). Alembic [env.py](env.py) loads settings and metadata.
The production-shaped local database is PostgreSQL 16 with pgvector, initialized by Compose.

## Change procedure

Revision `0040_knowledge_uploads` adds durable ingestion storage with deferred original bytes,
workspace ownership, states, leases and version linkage. Its isolated PostgreSQL migration test
verifies binary preservation, empty round-trip, invalid ready/empty-original rejection and refusal
of populated downgrade. This is storage groundwork; admission/extraction/worker integration is
tracked in the [active data administration plan](../../docs/exec-plans/active/data-processing-admin.md).
The local verification database has not yet applied this revision.

1. Name the entity owner, workspace scope, uniqueness and foreign-key requirements.
2. Add the model change and an Alembic revision in `versions/`; inspect generated SQL carefully.
3. Check existing data, nullability, backfill and index/locking cost before tightening constraints.
4. Test an empty-database upgrade and upgrade from the previous supported revision.
5. Verify foreign-workspace references and concurrent writes against PostgreSQL.
6. Document rollback or forward-repair strategy; do not assume downgrade is safe for user data.

From `backend/`: `uv run alembic heads`, `uv run alembic current`, `uv run alembic upgrade head`.
Container equivalent: `docker compose -p asi-verification exec -T api alembic current`.

## Current evidence and limitations

Revision `0037_retire_legacy_roles` converts Reviewer to Operator and Member/Developer
to Admin, following the approved four-role transition. Each changed membership gets an
audit record; a database constraint rejects future legacy assignments. This changes
authority and cannot be safely inferred backward, so downgrade refuses. Preserve a backup
before applying it and use forward repair or a verified restore for recovery.
The disposable PostgreSQL migration test verifies all three mappings, preserved users and
workspace, audit history, invalid-role rejection and downgrade refusal. The local app
applied 0037 after a successful 41-table restore drill; 104 Reviewer memberships converted
with 104 audit records. No legacy membership remains in that database.

Revision `0036_task_attempts` adds linked attempt provenance and retry request uniqueness.
PostgreSQL migration checks preserve prior applied notes through upgrade/empty downgrade,
and refuse to discard a populated retry's parent and multilingual correction. The local app
applied 0036 after preserving database-before-attempts.dump (349 archive TOC entries) in
the rebuild backup directory. Retry API, browser navigation and correction persistence pass.

Revision `0035_task_actions` adds internal proposals and notes. The isolated PostgreSQL
test verifies upgrade from 0034 preserves a multilingual task, permits empty downgrade,
and refuses downgrade after an applied note without losing its hash or content.
The verification app applied 0035 after preserving `database-before-actions.dump` in the
rebuild backup directory. Its archive listing verified successfully (330 TOC entries).
Full restore remains a separate release acceptance check.

Revision `0034_support_task_admission` adds task and execution admission records without
rewriting existing runs. Its isolated PostgreSQL test proves upgrade from 0033, empty
downgrade/re-upgrade, duplicate concurrent admission, and refusal to discard stored tasks.
The local verification stack applied 0034 for task endpoint/worker/browser integration.

Revision `0033_admin_operator_roles` adds Admin and Operator enum labels without
changing existing memberships. New UI assignments use Viewer/Operator/Admin/Owner;
legacy roles retained their original permissions until the approved 0037 transition above.
An isolated PostgreSQL test upgrades from 0032, preserves a legacy membership, assigns
Admin, and verifies concurrent owner departures retain one owner. Downgrade deliberately
refuses: prefer forward repair or restore a verified backup, never relabel authority.

Revision `0031_graph_step_sequence` adds a nullable sequence with per-run uniqueness and a
positive-value constraint. Existing steps remain null rather than receiving guessed order.
Deploy the migration before application code that reads the new field. Downgrade locks the
step table with a ten-second lock timeout and refuses while sequenced history exists; prefer
forward repair rather than deleting evidence. Acceptance is tracked in the
[ordering plan](../../docs/exec-plans/completed/graph-step-ordering.md).

Revision `0030_evaluation_reservations` supports either graph or evaluation ownership for model
admission, enforced by a check constraint. Existing graph rows retain their IDs and estimates.
Downgrade locks the reservation table and refuses while evaluation-owned rows exist, including
consumed/denied history. PostgreSQL tests exercise preservation, safe rollback and refusal.

Revision `0029_retrieval_outcome` adds outcome/error-code fields to retrieval traces. Existing
rows receive `unknown`, not an invented success status. Downgrade takes an exclusive table lock
with a ten-second timeout and refuses while failed/pending trace records exist; prefer forward
repair rather than erasing failure evidence. Tests preserve legacy query content through upgrade
and safe downgrade/re-upgrade, and verify refusal retains failed records.

The isolated stack applied revisions 0001 through 0025 on 2026-09-07. This proves clean
startup migration for that run, not upgrades of real deployed data or backup restoration.
The default pytest fixture uses SQLite `create_all`, so it bypasses Alembic and cannot prove
PostgreSQL locking, pgvector behavior or concurrency safety.

Revision `0026_model_call_reservations` adds reservation storage. Its isolated PostgreSQL
upgrade/downgrade/re-upgrade test is recorded in [testing](../../docs/testing.md); this is separate
from the older startup evidence above and does not establish safe rollback of deployed user data.

Services still have independent commit boundaries; review transitions and reservation admission
now have explicit transaction owners in the [service guide](../app/services/README.md).
Test conflicting sessions when changing those contracts. Keep test databases separate from
user databases; never reset a database merely to make an upgrade test pass.

Revision `0027_embedding_dimensions` widens `vector(16)` to `vector` without changing values.
PostgreSQL tests verify existing-vector preservation, safe downgrade/re-upgrade, 1,536-dimensional
ORM storage, and downgrade refusal without changing data or revision. Downgrade takes an exclusive
table lock and refuses if any vector has dimensions other than 16. Lock acquisition times out
after ten seconds; schedule migration during a controlled window and retry only after diagnosis.
Prefer forward repair once larger embeddings exist; this migration never deletes or truncates them.
Dimension-specific similarity indexes remain future work; see
[pgvector's mixed-dimension guidance](https://github.com/pgvector/pgvector#can-i-store-vectors-with-different-dimensions-in-the-same-column).

Revision `0028_ai_attempt_status` adds pending/uncertain ledger states. Its downgrade locks the
ledger and refuses while unresolved attempts exist; it never relabels them as success/failure.
The migration test verifies refusal preserves the pending record and revision, and verifies a
safe downgrade/re-upgrade once only terminal states remain. This is not an operator procedure
for reconciling provider charges or permission to overwrite unresolved production records.

See [schema design](../../docs/database-schema.md) and [testing](../../docs/testing.md).
