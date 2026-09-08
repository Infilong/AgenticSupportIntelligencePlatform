# Interrupted execution ownership

## State and scope
Embedding dispatch now uses the PostgreSQL ownership helper; migration 0032 persists nullable
execution_id/execution_protocol on AI ledger rows. Legacy rows remain unowned. An owner-only
recovery API now transitions orphaned pending attempts to uncertain with an atomic audit record;
Costs includes owner recovery controls; model-call integration is still open. The
[execution plan](../exec-plans/active/interrupted-call-recovery.md) owns acceptance; this does
not yet establish complete interrupted-call recovery.

## Ownership protocol
Generate an execution UUID before admission. Acquire a session advisory lock keyed by workspace
and execution on a dedicated PostgreSQL connection, then commit the acquisition transaction.
The session lock survives commits; no transaction or workspace row lock spans provider I/O.
Persist the attempt and protocol/ownership metadata only after acquiring ownership, so recovery
cannot claim a newly visible attempt before its dispatcher owns it. New embedding attempts
store protocol `pg-session-v1` and the lock's execution UUID. Admission and finish enlist a
Session on the owned connection before checking the lock, then commit independently of the
document/retrieval transaction. They reject an already-open connection transaction to avoid
joining one that their commit would not durably finish. Owned rows reject legacy finalization.

Before dispatch and completion, verify the original backend PID and held advisory lock. Never
reacquire ownership after reconnecting to complete a previous attempt. Completion must use the
owned connection for its transaction and verify ownership before mutating state. A separate
connection for the completion write creates a check/write race and is forbidden.

Recovery acquires the same lock without waiting. Busy means live ownership: reject recovery.
After acquiring, lock and refresh the scoped attempt and verify its supported protocol and
pending state. Transition an orphan only to uncertain usage with audit evidence; preserve the
admission estimate. Do not retry external calls, fabricate output, or release unknown costs.
Confirmed billing reconciliation is a separate authorized operator step. A recovering worker
must not publish the original result. Legacy pending attempts have no ownership proof and need
an explicit maintenance procedure; their age does not prove safety.

## Operator API
In Costs, select Recover on an eligible pending attempt, enter a reason, then submit recovery.
The server can reject a live owner. Failures retain the reason; manual refresh reconciles a
lost response with current state without replaying the request. After successful recovery,
select Reconcile only when billing evidence is available. Read-only roles and legacy pending
attempts have no recovery action.

Use `POST /workspaces/{workspace_id}/embedding-attempts/{attempt_id}/recover` with
`{"reason":"incident reference"}` and owner authentication. A 200 response preserves token/cost
estimates and reports uncertain usage. A live lock, unsupported legacy provenance or nonpending
state produces 409 without mutation. Membership and workspace state are checked again inside
the recovery transaction. Concurrent requests can produce only one transition/audit.

Recovery does not release usage or retry the provider. After independently confirming provider
billing, use the existing `/reconcile` action with confirmed tokens and an evidence reference.
That separate action records a failed attempt with reconciled usage, never successful vectors.

## Connection loss and fencing
PostgreSQL releases session locks when a backend terminates. A network partition can delay that
release; busy ownership remains conservative. The original connection must fail closed after
loss. A remote provider request may continue even after its database owner is gone, so lock
availability proves ownership loss, not absence of an external charge. Recovery retains unknown
usage, and a stale dispatcher must fail its completion transaction rather than publish vectors.

## Resource and operational limits
Each live execution consumes an additional database connection; configure concurrency and pool
capacity before rollout. Session advisory locks require direct PostgreSQL or session pooling;
transaction-pooling proxies are incompatible. The helper hashes workspace/execution UUIDs to
two positive int32 keys. A collision can conservatively block unrelated work; it cannot grant
two owners one execution. Cleanup releases the lock before returning the connection to the pool;
unverified cleanup invalidates the connection and emits a content-free diagnostic.

## Verification and remaining integration
Current tests exercise live exclusion, independent execution, release after exceptions, forced
termination of the exact test-owned database backend, stale-owner rejection, successor acquisition
and refusal to emulate distributed ownership with SQLite. Embedding integration tests inspect
committed pending metadata during transport, reject a competing owner, and terminate the exact
database owner to prove vectors cannot return and pending usage remains estimated. Migration
tests preserve legacy null metadata and reject destructive rollback once ownership history exists.
The process test terminates a dedicated mock-dispatch child, verifies live recovery rejection,
then recovers through the real API and separately reconciles synthetic billing usage. Tests
also cover permissions, audit rollback and concurrent single-transition recovery. Remaining work
includes broader crash windows, including partitions and failed
completion commits. Extend the protocol to model reservations as well
as embeddings; neither is finished by the ownership helper alone.
