# M3 — abandoned retrieval accounting

## Execution brief

Outcome / gates: TRACE/JOB must distinguish live inference from abandoned execution after a
process crash. Current synchronous retrieval traces and their embedding/reranking calls can
remain `started` forever; job reclaim only repairs calls directly linked to jobs. This is a
deep concurrency/recovery slice under the active M1–M6 goal, owned by root. Read root/backend,
docs and tooling guides; preserve existing authorization and the 04:44:58 UTC work cutoff.
Baseline linked-attempt checkpoint: `2e2054f`; its CI is running.

## Approach and constraints

- Hold a dedicated PostgreSQL session advisory lock across a retrieval, acquired before its
  trace becomes visible. No open database transaction during inference. Closing the dedicated
  connection releases ownership; do not infer death from elapsed time or wall-clock age.
- A bounded worker sweep may mark only abandoned started traces and their started calls as
  uncertain. Preserve finished calls, unknown usage/cost/timing, errors and workspace identities.
- Fence publication and subsequent dispatch if ownership is lost; a disconnected lock session
  alone does not prove CPU inference stopped. Do not overwrite uncertainty with an old result.
- Preserve the current permission checks and worker lease rules. No model/API spend, Redis,
  new service, destructive cleanup, merge or deployment. No private content in recovery logs.
- Reconcile legacy unowned records only after rebuilding/restarting the isolated runtime;
  older processes do not participate in the new ownership protocol.

PostgreSQL documents session versus transaction advisory-lock lifetime and cross-level conflict
in [explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS).
This primitive supplies ownership, not a complete recovery design; test the application's races.

## Verification and completion

Independent design/security review before finalizing implementation. Real PostgreSQL tests:
active calls survive sweeps, process termination releases ownership, abandoned records become
uncertain, terminal accounting is preserved, competing sweepers converge, and disconnected
owners cannot publish or launch another model call. Run a real child-process kill test without
external AI. Rebuild the development runtime and inspect correlated recovery evidence. Run
affected regression tests, update owning docs/receipts, commit/push and inspect CI. Broader
semantic routing, process-kill scenarios, imports, evaluation and restore remain separate gates.

## Previous checkpoint evidence

Linked attempts passed 91 PostgreSQL cases and combined eight-journey browser coverage, five
component tests, build/Ruff and 35 preparation checks. Preparation first failed on an unstaged
completed-plan move: `.artifacts/m0/prep-20260909T031835677980Z`; staging the intended rename
resolved the inventory error, with all 35 passing in `.artifacts/m0/prep-20260909T031912035069Z`.
No assertion or documentation check was weakened. All six independent freshness receipts passed.

## Repairs and current evidence

- Linked-attempt CI `34306686806` passed.
- Independent review required guarded model/trace writes as well as session ownership. Added
  trace-first accounting checks, safe retryable 503 responses, and bounded connection/statement
  settings with TCP keepalive options. Network detection timing remains platform-dependent;
  ownership loss is not proof that CPU work stopped.
- First focused run: four passed, one failed before child inference because the spawned fixture
  omitted identity-model registration. `.artifacts/m0/integration-20260909T032520855914Z` retains
  the failure. Added the same model registration used by the real worker; no runtime shortcut.
- Eight focused tests pass in `.artifacts/m0/integration-20260909T032835312259Z` (36.22s), including
  actual spawned-process termination, concurrent reconciliation, late embedding/reranker success
  and failure, active ownership, fair scans, completed accounting and safe connection-loss errors.
- The existing 91-test suite took 161.33s; the new eight-case recovery group takes 36.22s.
  The integration wrapper now allows 300 seconds instead of 180 for the expanded suite;
  per-operation assertions/timeouts and every other command's default remain unchanged.
- First full run: 99 passed, one failed in existing support cancellation setup with a missing
  handoff ID: `.artifacts/m0/integration-20260909T033036944703Z`. The helper previously ignored
  whether work was claimed and decoded an unchecked HTTP response. Added explicit claim/handoff
  preconditions with diagnostic state; no scheduling change, sleep or blind retry. Cause pending.
- 16 unit tests pass: `.artifacts/m0/backend-20260909T033312194706Z`. Independent final source
  review found no blocking issue. All four replacement services became healthy.
- Chrome run `7aee3f1a-94e2-4a18-bd71-505f8b1c53e4` reached development wait through actual local
  models; `.artifacts/m3/recovery-live-result.json` records successful trace, embedding and rerank,
  17/1417 input tokens and zero external charges. Correlated worker job
  `d000698d-98fe-4d27-9f3f-18d51985d535` logged success. This is a cold runtime smoke, not a new
  frozen quality/latency benchmark or full process-kill matrix.
- Final unchanged-snapshot regression: 100 passed in 186.85s,
  `.artifacts/m0/integration-20260909T033616695185Z`. All eight browser journeys passed in
  `.artifacts/m3/recovery-workbench-ui`; actual Chrome model accounting matched stored results.
  Ruff/formatting pass. The earlier cancellation case passed with diagnostic preconditions;
  its intermittent root cause remains unestablished, not fixed by a rerun.
- Observed Compose output replaced the old API and worker before starting the new worker in
  this run. The durable runbook now explicitly stops old producers first for the initial
  protocol transition rather than assuming replacement order for every deployment.
- Final independent documentation receipts and checkpoint pending. The next connected M3 gap
  is a human request-for-clarification decision preserving the draft and enabling a linked follow-up.
