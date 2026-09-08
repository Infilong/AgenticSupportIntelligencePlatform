# Interrupted call recovery
## Goal
Recover interrupted provider attempts without releasing possibly billed usage or racing live work.
## Context
Embedding attempts persist pending usage independently, but uncertain-only reconciliation cannot
recover orphaned pending calls. Model reservation expiry previously dropped unresolved allowance
from admission and permits evaluation deletion, even without proof of provider completion.
## Requirements
Retain unresolved usage until explicit finalization. Preserve workspace isolation and audit
evidence. Recovery must establish execution ownership loss, prevent stale completion from
overwriting recovery, and reconcile provider usage without automatic paid replay.
## Non-goals
Treating age as proof of death, fabricating vectors/answers, or silently forgiving unknown bills.
## Acceptance Criteria
Expired unresolved calls cannot free budget or permit deletion. Recovery rejects live attempts,
handles terminated workers, retains estimated usage until confirmed, and has PostgreSQL race
tests, permission checks, explicit errors and an operator workflow.
## Plan
1. Repair premature reservation expiry and verify admission/deletion regressions.
2. Design durable execution ownership and fenced completion for model/embedding dispatch.
3. Implement audited recovery, failure/permission/concurrency tests and operator workflow.
4. Verify end-to-end interrupted execution and update reliability/runbook evidence.
## Verification
Use mock transports and isolated PostgreSQL process/concurrency tests. Save before/after evidence
under .artifacts. Never infer terminated workers from elapsed time alone.
## Risks
Retaining unresolved allowance can block new spending until recovery exists. This is explicit
conservative accounting, not completed recovery. Database connection loss requires fencing;
process-local locks cannot protect multiple workers or survive restarts.
## Progress
2026-09-08 Costs recovery controls added with reason preservation, legacy/read-only restrictions,
separate billing confirmation and refresh handling after a lost response. Frontend build and
four focused browser tests pass after rebuilding the Compose frontend image. A full browser
run exposed an ambiguous status locator (fixed) and long initial navigation; the next run passed
28/29 with the editor test spending about 59 seconds navigating before exhausting its budget.
Content-free navigation timing diagnostics show about 56 seconds in Chromium DNS timing while
connection/server response take milliseconds. The diagnostic run passes 28/29 in
`.artifacts/embedding-recovery-ui-diagnostics.log`; full regression remains red. A shared-browser
loopback probe does not reproduce the stall, with or without resolver mapping. Continue the
[navigation investigation](browser-navigation-delay.md) before claiming full browser acceptance.
Model-call recovery and broader crash windows remain open. All processes have completed.

2026-09-08 owner recovery API: recover requires supported protocol and nonblocking ownership,
then rechecks membership/workspace/pending state and atomically records an uncertain transition
and audit. Estimates are retained; billing reconciliation remains separate. Ruff and 103
embedding/ownership tests pass in `.artifacts/embedding-recovery-broader.log` (120.89s), including
termination of a dedicated mock-dispatch process, real API recovery/billing flow, concurrency,
denied roles/foreign attempts, fresh membership and audit rollback. The rebuilt API is healthy.
Next: browser recovery controls and browser verification; model-call ownership/recovery and
broader partition/completion-failure windows remain open. All test processes completed.

2026-09-08 embedding integration: migration 0032 stores nullable execution UUID/protocol with
legacy nulls and guarded downgrade. Accounted embedding dispatch acquires ownership before
admission; admission/finish commit on the owned connection. Foreign owners, legacy bypass and
preexisting connection transactions are rejected. Lost owners cannot return vectors; estimated
pending usage remains. Ruff and 92 embedding/ownership/migration tests pass in
`.artifacts/embedding-ownership-broader.log` (135.39s). The rebuilt isolated API is healthy at
0032_execution_ownership head. Next implement audited orphan transition to uncertain usage,
permission/lock-race checks and application-process crash proof, then model-call integration.

2026-09-08: inspected embedding admission/finish/reconciliation and model reservation lifecycle.
Reproduction in `.artifacts/reservation-expiry-before.log`: two failures and 19 passes prove
expiry allowed budget reuse and evaluation deletion. Removed expiry predicates from admission
and deletion; explicit finalization remains. Broader PostgreSQL-enabled budget/provider/
embedding regressions pass 119 tests in `.artifacts/reservation-expiry-verified.log` (103.11s),
with Ruff and repository checks passing. All processes completed. Next: design execution
ownership and fenced completion, then implement operator recovery; retention alone is not recovery.
2026-09-08: [ownership design](../../design-docs/interrupted-execution-ownership.md) and
`execution_ownership.py` helper added. Ruff and four isolated PostgreSQL tests pass in
`.artifacts/execution-ownership-verified.log` (3.44s): live exclusion, exception release,
terminated database owner rejection/successor acquisition and unsupported-backend refusal.
Cleanup does not reconnect an invalidated owner. The helper is not yet used by dispatch.
Next: persisted protocol metadata and embedding admission/completion integration using the
owned connection, followed by audited recovery and application-process crash tests.
## Decisions
Expiry is operational metadata, not evidence that a provider was never dispatched or unbilled.
## Findings
The previous expiry exclusion is repaired. Ownership proof must cover the completion write on
the owned connection; checking a lock before writing through another connection leaves a race.
## Final Result
Open; recovery requires all acceptance criteria, not only the first accounting repair.
