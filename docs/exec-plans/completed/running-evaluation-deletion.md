# Protect running evaluations from deletion
## Goal
Prevent permanent deletion of evaluations whose execution has not reached a terminal state.
## Context
The existing deletion guard checks active reservations. A running evaluation can have only
consumed reservations between case execution and final metrics/status publication.
## Requirements
Return typed 409 for running evaluation deletion; preserve archive/read behavior and active
reservation protection. Completed archived evaluations must remain deletable.
## Non-goals
Cancellation, restart/resume, stale-running reconciliation or automatic forced deletion.
## Acceptance Criteria
API conflict preserves all rows. A paused real PostgreSQL evaluation survives attempted
deletion after its model call, completes with results/metrics, and can then be deleted.
## Plan
1. Reproduce API and PostgreSQL failures without the guard.
2. Add running-state validation and route error mapping, preserving source-size limits.
3. Run affected permission/transaction/reservation tests and inspect live integration.
## Verification
Mock providers, real PostgreSQL overlap, API snapshots, Ruff and repository checks.
## Risks
An orphaned running evaluation will remain protected until a separate recovery workflow exists.
Do not treat elapsed time as evidence that provider work stopped or is safe to delete.
## Progress
2026-09-08: inspected lifecycle and reservation guard; added two reproduction tests.
Both failures reproduced. Added running-state conflict, preserved reservation precedence and
consolidated route 404 handling to lower its size limit. Ruff and 30 affected tests pass with
PostgreSQL; rebuilt API passes four browser checks and 543 HTTP outcomes without server errors.
Exact commands and artifacts: [testing](../../testing.md#running-evaluation-deletion-protection).
## Decisions
Archive remains a reversible visibility operation. Permanent deletion requires terminal state.
## Findings
The original guard did not inspect EvaluationRun.status. Consumed reservations left an actual
execution gap in which evaluation deletion succeeded. The lifecycle guard closes this gap.
## Final Result
Completed 2026-09-08 for deletion protection. Paused execution survives rejection and completes;
terminal archived deletion remains available. Orphaned-run recovery remains separate release work.
