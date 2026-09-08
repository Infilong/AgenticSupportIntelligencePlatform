# Evaluation baseline budget admission

## Goal
Stop direct/vector-RAG evaluation generation from bypassing shared model-call budgets.
## Context
At inspection graph calls used BudgetedModelProvider, while direct/vector baselines used
ConfiguredModelProvider. Reservations required graph_run_id without baseline evaluation context.
## Requirements
Reserve before baseline model dispatch. Share monthly accounting with graph calls; aggregate
baseline reservations/ledger usage by evaluation run for per-run policy checks. Persist denials,
provider success/failure and reservation reconciliation without holding locks during provider I/O.
## Non-goals
Changing system-v1 graph per-run semantics, real-provider billing certification, or auto-retries.
System-v1 retains graph budgets; this change does not introduce a combined graph/baseline batch cap.
## Acceptance Criteria
Direct/vector baselines deny exhausted budgets before dispatch. Successful calls reconcile usage;
uncertain calls retain allowance according to existing policy. PostgreSQL overlapping evaluation
and graph reservations share monthly admission. Migration preserves existing graph reservations
and refuses destructive downgrade when evaluation reservations exist.
## Plan
1. Reproduce missing admission with provider observation tests.
2. Add evaluation context to reservation schema, validate workspace/run context and reuse admission.
3. Route baseline generation through BudgetedModelProvider and preserve explicit result errors.
4. Verify focused behavior, concurrency, migrations, broader tests and browser journeys.
## Verification
Keep .artifacts/evaluation-budget/ reproductions and final logs. Run focused budget/evaluation
tests, PostgreSQL overlap/migration checks, lint, backend suite, browser journeys and doc/size gates.
## Risks
Wrong workspace associations, double accounting and premature release after uncertain provider
errors. Baseline RAG embedding admission is separate; model-call admission must not bypass it.
Evaluation deletion must not discard an active reservation. No provider I/O under workspace locks.
## Progress
2026-09-08: inspected current evaluation/provider/reservation boundaries and added denial regressions.
Both baseline modes dispatched despite exhausted monthly budgets before the repair. Added
migration 0030 and shared baseline admission, cumulative usage and active-reservation deletion
protection. Extracted direct baseline generation; EvaluationRunner shrank from 553 to 545 lines.
Focused provider tests passed (25), PostgreSQL budget/migration checks passed (25), and the full
backend suite passed 427 tests in 269.07s. CI-equivalent lint passes after formatting fixes.
The first browser run passed 23 tests but the toast test refreshed before workspace bootstrap
was guaranteed complete; retained its trace and added the missing ready-workspace precondition.
Final browser suite: 24 passed in 55.5s. Final API window records 2,222 HTTP outcomes with zero
server failures. Migration 0030 is current; providers remain mock with no API key. All 17 tooling
tests and documentation/source-size/whitespace gates pass. See
[testing](../../testing.md#evaluation-baseline-budget-admission) for commands and saved artifacts.
## Decisions
Extend the shared reservation table with exclusive graph/evaluation ownership; do not create
synthetic graph runs merely to reuse accounting. Keep focused helpers if legacy files would grow.
## Findings
Both baseline generators bypassed BudgetedModelProvider at inspection. The full browser run
exposed a pre-existing harness race after Refresh became available during bootstrap. Its timer
assertions remain unchanged; the fixture now awaits the workspace name and permitted navigation.
## Final Result
Completed 2026-09-08. Baseline generation now reserves shared monthly and baseline-run allowance
before dispatch, links actual model usage, records denial without an answer/call, and blocks
deletion while allowance is active. PostgreSQL tests prove evaluation/graph competition and
safe migration preservation/refusal. Existing graph behavior remains covered by the full suite.
Combined system-v1/baseline batch caps, embedding attribution per evaluation, exact external
billing and crash-safe recovery remain outside this repair. The production goal stays active.
