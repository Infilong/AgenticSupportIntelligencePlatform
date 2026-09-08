# Reliability contract

These are required engineering behaviors, not a claim that every path meets them today.
[Quality score](QUALITY_SCORE.md) records gaps; [testing](testing.md) records evidence and commands.

## Explicit failures
`evaluation_execution.py` owns metric publication and unexpected evaluation failure finalization.
It rolls back unfinished writes, attempts `failed` status with completion time, then re-raises
the original error. Previously committed results and model usage remain. Failure to persist
that status is explicit in content-free diagnostics; a persistent outage or process death can
still leave a running record. It does not retry models, resume execution or guarantee recovery
after an ambiguous commit acknowledgment. See [evidence](testing.md#evaluation-terminal-failures).

Return actionable, typed errors at boundaries. Do not swallow broad exceptions, substitute
fake success, or silently omit failed model/tool work. Persist terminal failures where possible;
re-raise unexpected exceptions to the owning handler. Never expose secrets or internal stack
traces to clients. Failed mutations must preserve recoverable user drafts and explain retry.

The browser treats authenticated HTTP 401 as session rejection and returns to sign-in, clearing
scoped state. Root generation checks prevent an old failure from expiring a newer login. Login
credential errors, 403, network and 5xx failures do not expire sessions. Background read errors
are shown; Refresh retries account discovery even without a selected workspace. Session changes
clear drafts; ordinary failed reads and permission denials retain them. There is no automatic
mutation replay or token-refresh flow. See [session recovery evidence](testing.md#session-recovery).

## Timeouts and retries
Bound network/provider timeouts and total operation deadlines. Retry only transient failures
when the operation is idempotent or has a persisted idempotency key; use bounded attempts and
backoff. Never blindly retry permission denial, invalid input, payments or model calls with
uncertain usage. Record attempts and distinguish retryable failure from terminal failure.
Local HTTP startup polling is bounded; it does not establish database/queue recovery health.

## Observability
Follow [observability design](observability-design.md) for log/record shapes. Correlate requests,
graph steps, retrieval and model attempts; capture outcome, duration and attributable usage.
Use route templates and scrub sensitive data. HTTP request IDs link to created graph/trace IDs
through structured workflow events; graphless calls, distributed correlation and global log
redaction/retention remain incomplete. Keep diagnostic artifacts ignored
and use synthetic data; review traces before sharing. Never claim all server logs are sanitized.

## Database integrity and permission boundaries
Permanent evaluation deletion requires a non-running state as well as no active model-call
reservation. This protects gaps between model calls and final publication; archiving does not
cancel execution. A paused PostgreSQL evaluation completes safely after a rejected deletion.
Orphaned running records remain protected pending explicit recovery tooling. See
[running evaluation evidence](testing.md#running-evaluation-deletion-protection).

Evaluation move/archive/permanent deletion and their actor-attributed audits share one commit
through `evaluation_management.py`. Audit persistence failure rolls back evaluation children
and reservation-reference changes; PostgreSQL observers verify no pre-commit visibility and
retry produces one audit. Routes supply the authenticated actor; the active-reservation deletion
guard remains. This does not prove concurrent execution recovery or ambiguous commit handling.
See [evaluation audit evidence](testing.md#evaluation-management-audit-atomicity).

Human label upsert locks the scoped conversation with PostgreSQL NO KEY UPDATE before querying
the label, including when no human label exists yet. The label query refreshes cached ORM state.
Edits serialize with last-writer-wins semantics; ordinary reads remain unlocked. This prevents
first-create collisions and stale-value restoration failures, not conflicts between user intent.
See [label concurrency evidence](testing.md#concurrent-human-label-edits).

Dataset moves/deletes use `dataset_mutation.py` to commit actor-attributed audits with the
mutation. Audit failure rolls back dataset and child records; PostgreSQL observers and retry
tests cover this boundary. Import/label audit coverage and concurrent editing remain separate.
See [dataset management evidence](testing.md#dataset-management-audit-atomicity).

Dataset imports validate the entire parsed batch's example/message languages before inserting
usable examples, messages or labels. Validation failure preserves a failed import batch and
empty dataset for diagnosis, rather than committing a partially usable prefix. Previously
imported rows remain unchanged. Corrected input can be imported as a new batch; this is not
in-place retry or a guarantee about arbitrary database failures.
See [validation failure evidence](testing.md#dataset-import-validation-atomicity).

Backend owns transaction boundaries. Use constraints plus atomic transitions/locking when
concurrent writes can violate ownership, budget or review state. Verify on PostgreSQL, not only
SQLite. Migrations need upgrade/recovery evidence; multi-write failures must not leave success
claims over partial state. Authenticate and enforce workspace membership/permission before
protected data enters queries, retrieval ranking, tools or model context. Test cross-workspace
and denied-role cases, including folder assignment and resource management.

First-use budget policy initialization locks the workspace with NO KEY UPDATE after observing
a missing policy, then rechecks before insertion. This serializes Costs/policy readers with
embedding and graph admission initializers. The initialization branch commits before returning
even when another caller created the policy, so its lock does not span provider I/O. Existing
policy reads do not acquire this initialization lock. PostgreSQL synchronized regressions cover
competing policy reads and embedding admission; SQLite alone cannot establish this guarantee.

Review claim/release/resolve acquire a PostgreSQL row lock before checking assignment and terminal
state. The query refreshes cached ORM values. Review, graph outcome, checkpoint and audit commit
together; failed persistence rolls back and re-raises the original error. Request-session cleanup
releases locks on rejected transitions. This guarantee is verified on PostgreSQL; SQLite tests
cover API behavior but cannot prove row-lock semantics. Agent model-call admission and reservation
reconciliation also serialize on a workspace row; see [token economy](token-economy-design.md)
for estimates and evaluation-mode limits. Reserved allowance does not expire automatically:
age cannot prove absence of billed usage or live execution. Expired unresolved reservations
continue to block conflicting spending and evaluation deletion until explicit finalization.
See the [interrupted-call recovery plan](exec-plans/active/interrupted-call-recovery.md) for
the remaining ownership/fencing and operator-reconciliation work.

Final graph publication is owned by `graph_outcome.py`: final guardrails, run status/answer and
any required review queue entry commit together. Publication errors roll back and attempt to
record `failed` / `publication_failed` without an answer, then re-raise the original error.
If storage also rejects that failure record, a content-free error-type log records the secondary
failure. Process termination or a persistent database outage can still leave `running` records;
this is not durable resume, idempotent recovery or proof about lost commit acknowledgments.

Folder parent updates acquire a workspace `NO KEY UPDATE` lock and inspect current,
workspace/type-scoped ancestry before mutation. Descendant or cyclic ancestry returns an
explicit invalid-folder error. Fresh reads prevent cached ORM state from hiding a competing
move. The lock lasts until commit/rollback; rejected API requests release it during session
cleanup. PostgreSQL opposing-move and stale-session tests cover this boundary.
Folder create/update/delete stage the folder and its attributable audit in one transaction;
failed persistence rolls back and re-raises. Separate-connection PostgreSQL tests verify that
flushed changes remain invisible before audit commit and that failures permit a corrected retry.
Resource assignment/deletion races and ambiguous commit acknowledgments remain separate concerns.

## AI/model failure handling
Reindex, move and delete lock the workspace-scoped document with PostgreSQL NO KEY UPDATE
and refresh cached ORM state before mutation. Reindex allocates its version only after that
lock, so overlapping reindexes cannot select the same next version. Ordinary reads do not
acquire the mutation lock. The lock spans indexing provider I/O until commit/rollback;
production lock-wait/whole-operation deadlines and crash recovery remain separate concerns.
See [concurrency evidence](testing.md#concurrent-knowledge-reindexing).

Document moves and deletions now commit their actor-attributed audit with the mutation through
`knowledge_mutation.py`. Audit failure restores document/index state and allows a corrected
retry; PostgreSQL visibility tests cover the uncommitted boundary. Successful upload/reindex
publication also commits its audit atomically. API calls pass the authenticated actor; internal
reindex operations without an actor record a null actor. Audit failure rolls back publication
while independently committed embedding usage survives. Provider failures retain explicit failed
document status. See [index publication evidence](testing.md#knowledge-indexing-audit-publication).

Use deterministic/mock providers in automated tests. Enforce input/output budgets before calls,
record successful and failed attempts in the AI ledger, and retain retrieval/graph trace links.
Use packed evidence rather than raw long documents. Explicitly route unsafe, unsupported or
low-confidence answers to human review. Guardrails and citation presence alone do not establish
answer quality. Provider timeout, malformed output, refusal and accounting failure need tests.
Real-provider verification requires separately authorized credentials/spend and controlled cases.

## Regression and runtime verification
Reproduce a failure, preserve its evidence, add a behavioral regression, then repair the owning
boundary. Make recurring setup failures improve scripts/CI rather than increasing test retries.
Run the relevant checks, review the diff and record exact limits. The local verification runner
captures command outcomes and runtime/browser artifacts; CI browser execution is defined but
not yet verified remotely. Never treat a live process, health response or successful build as
proof of the complete README journey.

Before release, demonstrate restart/recovery, backup restoration, migration safety, concurrency
and workload targets. Redis startup does not mean worker execution exists; stored graph
snapshots do not mean workflows can resume after a crash. See the
[active production plan](exec-plans/active/production-readiness.md) for remaining release work.
