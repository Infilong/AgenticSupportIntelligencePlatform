# Run budget enforcement

Historical expiry behavior below is superseded by the
[interrupted-call recovery work](../active/interrupted-call-recovery.md): unresolved reserved
allowance now survives expiry until explicit finalization. Other evidence remains historical.
## Goal
Enforce agent/workspace run and monthly token/cost budgets before model calls with reservations.
## Context
At the start, the [design ticket](../../tickets/run-budget-reservations.md) was unimplemented:
model planning checked only context, despite passing an effective run limit in state.
## Requirements
Persist reservations and denials; serialize admission across a workspace; account for ledger and
active estimates without counting consumed reservations twice. Link successful/failed provider
ledger rows, release known pre-call failures, and bound abandoned reservations. Enforce runtime
at both classification and drafting; denied calls must not invoke a provider and must reach review.
## Non-goals
Provider billing reconciliation, distributed rate limiting or infrastructure expansion.
## Acceptance Criteria
All criteria and failure/permission cases in the linked design ticket pass, including PostgreSQL
concurrency, migration upgrade, full backend tests, and actual graph/provider integration.
No claim of enforcement until both model-call sites are wired and tested.
## Plan
1. Implement the reservation model, migration and serialized accounting service.
2. Verify limits, ledger reconciliation, isolation, expiry and concurrent admission.
3. Integrate the provider boundary with explicit budget errors and bounded requested output.
4. Verify graph routing, traces, migrations, full tests and browser behavior.
## Verification
Deterministic providers; scoped tests plus real PostgreSQL overlap tests in isolated schemas.
Migration upgrade/downgrade on a disposable database. Preserve evidence under
.artifacts/20260907-budget-reservations/; hosted CI remains separately unverified.
## Risks
No lock may span a network call. Prompt estimates are approximate; output must be bounded.
Unknown provider outcomes cannot safely release spending immediately. Expiry trades conservative
blocking for possible late accounting; do not claim exact external billing guarantees.
## Progress
2026-09-07: confirmed the enforcement gap. Added storage/service draft; runtime integration is open.
Reservation storage and admission service pass nine PostgreSQL tests; migration upgrade,
downgrade to 0025 and re-upgrade pass in a disposable database (10 tests combined). Final lint
passes. A focused finalization-lock regression was added afterward. No provider/graph call site
was connected at that stage; it was not evidence of runtime enforcement.
The finalization-lock regression passes against PostgreSQL; evidence: finalization-lock.log.
Classification and drafting now use BudgetedModelProvider. Corrected old-boundary regressions
fail all six cases; integrated boundary passes. Initial fixtures accidentally used /run instead
of /runs; retain those setup failures without treating them as behavioral evidence.
Real transport cap, incomplete/invalid usage, timeout retention and concurrent dispatch are
covered by the 25-test focused run. Twelve reservation/isolation/context tests pass. Browser
journeys pass 3/3, and live migration reports 0026 head. Initial full suite passed 270 tests
before review added further usage/concurrency cases. Final full suite passes 277 tests in 136.49
seconds (full-final.log), including PostgreSQL and migration checks; lint and structural gates pass.
## Decisions
Lock the workspace row, which exists even before policy creation, to avoid missing-policy races.
Persist denied requests as denied rows with a stable reason; they do not reserve budget.
Finalization takes the same workspace lock as admission to prevent a split ledger/reservation
snapshot from losing usage. During the provider-ledger/finalization interval, usage can be
conservatively counted twice; consumed reservations themselves are excluded from totals.
Real dispatch with no ledger is not evidence of zero spend. Retain unknown allowance until
expiry; release only known mock pre-ledger failures. This corrects the design ticket's overly
broad pre-ledger release rule. Missing/partial successful usage is also uncertain and retained.
Provider completion requests are capped; prompt estimates are conservative, not billing-exact.
## Findings
The initial provider had no completion cap; runtime now supplies it. Independent review found
that successful responses lacking complete usage freed allowance too early. The fix preserves
usage completeness and retains uncertain reservations; re-review found no scoped P0/P1.
## Final Result
Completed 2026-09-07: classification and drafting reserve before dispatch, share run/month limits,
and route denied calls to review without creating AI calls. Output caps and ledger reconciliation
are verified; uncertain usage retains allowance until expiry. Evidence is in the two budget
artifact directories above. Exact billing, rate-limit concurrency and non-agent evaluation
admission remain outside scope; this does not complete the broader production objective.
