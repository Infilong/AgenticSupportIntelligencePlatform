# Testing and runtime evidence

## Current rebuild acceptance

Use the [acceptance audit](audits/simple-admin-acceptance.md) for the current five-area app.
It records the completed compiled-browser 28-test suite, PostgreSQL 15-test selection,
backend full-run evidence plus its resolved Windows parameter-ID issue, CLI operations,
and schema-0037 restore drill. Earlier sections remain dated historical evidence.
No real-provider or unconditional production readiness is implied.

## CLI acceptance
2026-09-08: `pytest tests/test_cli.py tests/test_cli_http.py -q` passes 14 checks in
2.86s. Tests cover Windows DPAPI/POSIX session protection, API binding, no printed secrets,
UTF-8 transport, upload limits, redirect refusal, permission exit codes, request-key
retention, and watch timeout/review behavior. The initial Windows newline assertion compared
binary-preserved CRLF with text-mode LF; it now checks the actual uploaded bytes decoded as UTF-8.
Scoped Ruff passes. The installed `asi` entry point uses the existing backend build system.
Local installation required a workspace uv cache and permitted access to the existing
setuptools build dependency; no CLI runtime dependencies were added.
`.artifacts/cli-live-evidence.json` records 27 live command checks against mock providers in
workspace `fb1e2db3-e503-45bb-bd94-54265b00eafa`: login, workspace/agent lists, ingestion,
task creation/watch/inspect, exact-hash action approval, answer approval/rejection, stop,
and viewer denials. Runs: approved `37df448c-98e8-4140-9bf7-5ad060fc1003`, rejected
`d7b82d6e-4952-4696-beed-a216eb842770`, stopped `61cbf975-4816-4ea9-8b8a-77db44d156a2`.
Credential material is excluded from the evidence report. Real-provider acceptance remains separate.

## Retry browser and API acceptance
2026-09-08: retry/task API and admission tests passed 9 checks in 6.82s. Five rebuild
browser journeys passed in 39.2s, including new corrected attempt, reload, original/follow-up
navigation, action review and membership denial. TypeScript/Vite and scoped Ruff passed.
The app runs migration 0036 after a fresh database backup with a verified archive listing.
Chrome retry `5004c0d6-2d1a-4872-a671-95e56ff058c8` completed and retained its correction;
SQL confirms its parent remains stopped. Further retry `64067172-b91d-4f89-9ebf-f9778a13853e`
showed existing-note reuse. SQL confirms one task note and reused=true, not a duplicate write.
No Chrome console errors during retry inspection. Mock quality remains distinct from real-provider acceptance.

## Linked-attempt backend
2026-09-08: `pytest tests/test_task_attempts.py tests/test_task_attempts_postgres.py -q`
with PostgreSQL enabled passed 9 checks in 13.93s. They prove caller-bound request replay,
unchanged parent/configuration, permission/active-run denial, concurrent duplicate/distinct
retry admission, reuse of an applied note, and actual worker prompts containing the human
correction and bounded task history. Four migration/concurrency checks passed in 28.66s,
preserving prior notes and refusing loss of a populated 0036 retry history.
New task rejections persist rejected via extracted review_outcome; legacy review/API
regressions passed 27 checks in 43.41s. Scoped Ruff passed. API/UI deployment remains pending.

## Browser internal action acceptance
2026-09-08: `FRONTEND_URL=http://localhost:5174 npm run test:e2e -- rebuild-actions.spec.ts
rebuild-core.spec.ts rebuild-knowledge.spec.ts rebuild-members.spec.ts --workers=1` passed
5 journeys in 36.5s. Final action-layout rerun passed in 11.9s. TypeScript/Vite passed.
Chrome approved two proposals in run `8f00938a-2713-4b09-87b3-75c6559385c6`; SQL confirms
two applied actions and one note. Rejected run `d4e2ebdb-9798-4859-bd29-b9bfa86dce02` and
stopped run `c823b7fa-603e-441c-b07c-8c6d4c290f4c` each have two rejected actions and no notes.
Chrome console inspection returned no errors. The app runs migration 0035 after a fresh
database backup. These runs use mocks; real-provider acceptance is still pending.

## Action worker and API integration
2026-09-08: two action HTTP tests pass for inspection, role denial, exact hash, duplicate
resolution and answer-review bypass prevention. Full mock PostgreSQL worker tests produce
two proposals from grounded outputs, apply them only after approval and publish the cited
answer; an unsafe request produces none. The expanded worker/review/stop command passes
17 tests in 19.07s. Initial run failed one stop-versus-review race with a real workspace
lock/checkpoint foreign-key deadlock; evidence is in `.artifacts/task-action-stop-deadlock.txt`.
Stop/action workspace locks now use FOR NO KEY UPDATE. A targeted regression holds that
lock while review inserts its checkpoint and passes in 1.33s. No concurrency assertion
was weakened. Browser integration and deployment remain pending.

## Internal action transaction foundation
2026-09-08: `pytest tests/test_task_actions.py -q` passes 11 cases: exact approval,
deduplicated note/category changes, rejection, stale hash, unknown proposal, authority
revocation, removed capability, stop, tampered inputs and storage rollback.
With `RUN_POSTGRES_TESTS=1`, `test_task_actions_postgres.py` passes 2 concurrent
approval/stop cases. `test_task_actions_migration.py` plus action, stop and knowledge
tests passed 17 checks before the final independent-reviewer case was added.
The migration test uses a disposable database and proves task preservation and refusal
to discard applied history. Scoped Ruff, docs and diff checks pass. Existing httpx warning
remains. These are service/schema checks; action graph/API/UI integration is pending and
revision 0035 has not been applied to the running app.

## Rebuild agent knowledge selection
2026-09-08: `pytest tests/test_agent_knowledge_scope.py tests/test_retrieval.py
tests/test_retrieval_versions.py tests/test_retrieval_failures.py tests/test_langchain_support.py -q`
passed 20 tests, with 4 PostgreSQL-only skips. Repeating version/failure tests with
`RUN_POSTGRES_TESTS=1` against the local verification PostgreSQL passed all 7 tests.
New checks prove foreign document IDs are rejected, duplicates normalize, selection can
be cleared, excluded text never enters mock prompts, and empty selection yields review.
`FRONTEND_URL=http://localhost:5174 npm run test:e2e -- rebuild-core.spec.ts
rebuild-knowledge.spec.ts rebuild-members.spec.ts --workers=1` passed 4 tests in 26.1s.
TypeScript/Vite build and scoped Ruff passed. Existing Starlette/httpx warning remains.
Chrome selected one document, saved/reopened settings and completed run
`76832cb1-afe6-48f4-b61d-876120da3939` with that source, 789 tokens and no console errors.
Mock-provider evidence only. The active rebuild plan tracks remaining acceptance gaps.

## Costs recovery UI and navigation regression
2026-09-08: frontend build passes. Four focused browser tests pass in 17.4s
(`.artifacts/embedding-recovery-ui-verified.log`) after rebuilding the Compose frontend image.
The first run exercised an old baked image (2 passed/2 failed); the frontend guide now documents
the rebuild requirement. Tests simulate only embedding responses while auth/workspace/Costs
requests remain live. They cover retained reasons after live-owner/network failures, separate
billing confirmation, read-only and legacy restrictions, and refresh after an applied mutation
with a lost response without replay. The recovered-page screenshot was visually inspected.

Full 10-worker verification exposed an ambiguous recovery status selector (fixed to target its
notice) and long navigation. Subsequent runs pass 28/29 with the editor test spending about
59 seconds in initial navigation. Latest evidence: `.artifacts/embedding-recovery-ui-diagnostics.log`.
Raw CDP diagnostics report roughly 55.8 seconds in DNS timing for loopback, followed by a few
milliseconds for connection and response; no proxy/SSL phase. Existing assertions/timeouts remain.
A shared-browser probe passes all 20 navigations under 1012ms, with/without explicit resolver
mapping (`.artifacts/loopback-dns-probe.json`); this does not explain multi-worker failure and
no flag was added. Strict typing of the diagnostic fixture and repository checks pass.
The [navigation plan](exec-plans/active/browser-navigation-delay.md) owns the unresolved failure.

## Embedding orphan recovery API
2026-09-08: the owner recovery endpoint transitions owned orphaned attempts from pending to
uncertain without changing token/cost estimates. It rejects live execution, legacy ownership,
nonpending state, archived workspaces and denied roles. Membership is rechecked in the write
transaction; transition/audit writes commit together. Two concurrent requests record one audit.

Ruff and `uv run --frozen --extra dev pytest -q tests/test_embedding*.py
tests/test_execution_ownership*.py` pass 103 tests (120.89s) in
`.artifacts/embedding-recovery-broader.log` with PostgreSQL enabled, mock transports and no
OpenAI API key. A dedicated child runs accounted mock dispatch: the real API denies recovery
while it is alive, the test terminates and joins only that child, recovery retains 13 estimated
tokens, and a separate reconciliation records confirmed synthetic usage. Audit-failure rollback
and retry, permission denials and foreign-attempt rejection are covered. The existing
Starlette/httpx warning remains. Repository checks pass over 179 source files.

The isolated API rebuild succeeds (`.artifacts/embedding-recovery-startup.log`) and health
readiness passes. No browser run: pending recovery controls are not yet in the Costs UI.
Model-call recovery, legacy recovery and partition/failed-completion windows remain open.

## Owned embedding dispatch and migration 0032
2026-09-08: migration 0032 adds nullable execution UUID/protocol without assigning ownership
to legacy history. Embedding dispatch acquires the lock before publishing admission and commits
admission/finalization through the owned connection. Tests inspect committed pending metadata
during mock transport, exclude a competing owner, terminate the exact test-owned database
session, and prove no vectors return while estimated pending usage remains. Owned rows reject
legacy finalization; foreign owners and accidental outer transactions are rejected.

Ruff and the PostgreSQL-enabled command `uv run --frozen --extra dev pytest -q
tests/test_embedding*.py tests/test_execution_ownership*.py
tests/test_evaluation_reservation_migration.py tests/test_graph_sequence_migration.py` pass
92 tests in 135.39s (`.artifacts/embedding-ownership-broader.log`). The initial focused run
passed 17 tests; the broader run includes the additional transaction/scope check. Migration
tests verify legacy values, metadata constraints, safe empty-history downgrade and refusal to
erase ownership history. Existing Starlette/httpx deprecation warning remains.

The isolated API was rebuilt with mock providers via `docker compose -p asi-verification up
-d --build --no-deps api` (`.artifacts/embedding-ownership-startup.log`); readiness passes and
`docker compose -p asi-verification exec -T api alembic current` reports
`0032_execution_ownership (head)`. Repository checks pass. No browser rerun; operator recovery,
application-process crash recovery and model-call ownership remain unimplemented.

## Provider execution ownership foundation
2026-09-08: Ruff and `uv run --frozen --extra dev pytest -q tests/test_execution_ownership.py`
pass four tests in 3.44s (`.artifacts/execution-ownership-verified.log`), using the isolated
PostgreSQL fixture with RUN_POSTGRES_TESTS=1. Tests verify that live ownership excludes a
competitor, another execution can proceed, exceptions release the session lock, and terminating
the exact test-created database backend makes the original owner unusable while permitting
a successor. SQLite is rejected. Cleanup avoids reconnecting a lost owner and invalidates a
connection whose lock cleanup cannot be verified. The existing Starlette/httpx warning remains.

The helper is not yet integrated into provider dispatch; this does not prove application-worker
crash recovery, finalization fencing or an operator recovery workflow. Those requirements stay
in the [ownership design](design-docs/interrupted-execution-ownership.md) and active recovery plan.
Repository checks pass over 178 source files. No browser or full-suite rerun for this foundation.

## Unresolved reservation expiry retention
2026-09-08: `.artifacts/reservation-expiry-before.log` reproduces two failures and 19 passes:
expired unresolved reservations allowed budget reuse and permanent evaluation deletion. Admission
and the deletion guard now retain all reserved rows until explicit finalization, irrespective
of expiry. The existing release/consume paths still work; no provider calls are replayed.

Ruff and `uv run --frozen --extra dev pytest -q tests/test_budget*.py
tests/test_evaluation_budget*.py tests/test_embedding*.py` pass 119 tests (103.11s) in
`.artifacts/reservation-expiry-verified.log`, using PostgreSQL enabled, mock transports and an
empty OpenAI key in the isolated Compose API container with current app/tests mounted read-only.
Coverage includes concurrent admission/finalization, denied workspace access, provider failures,
embedding accounting and both expired/unexpired deletion guards. The Starlette/httpx warning
remains. Documentation/source-size/whitespace checks pass. No browser rerun for this backend
repair. Orphaned calls can still block spending; the
[recovery plan](exec-plans/active/interrupted-call-recovery.md) remains open for ownership,
fencing and operator reconciliation.

## Evaluation loaded-case identity
2026-09-08: after correcting the new test's response-envelope lookup, API regressions reproduced
three misleading comparisons for changed questions, changed limits and added duplicate cases;
reordered cases already passed (`.artifacts/evaluation-identity-reproduced.log`, 3 failed/1 passed).
Scoring now stores canonical loaded-case fingerprints and contract v2; comparisons require
identical per-mode/language fingerprint multisets. Existing results are not backfilled.

Ruff and `uv run --frozen --extra dev pytest -q tests/test_evaluation*.py` pass 103 tests in
75.66s (`.artifacts/evaluation-identity-final.log`) with PostgreSQL enabled, mock providers and
an empty OpenAI key in the isolated Compose API container. Tests prove reordered-case
comparability, changed-input/expectation/multiplicity rejection, and canonical metadata order
with sensitivity to language/expectations/limits. Repository checks pass over 177 source files.
The existing Starlette/httpx warning remains. No UI edits or browser rerun for this increment;
the earlier full pipeline below predates case fingerprints. Prompt/model/knowledge configuration
equivalence is not established by this check. See the
[comparison contract](evaluation-design.md#comparison-contract-provenance).

## Full regression after evaluation contract repairs
2026-09-08: `./scripts/verify.ps1 -PythonExecutable
'C:/Users/ytxqf/AppData/Local/Programs/Python/Python312/python.exe'` passes all 17 gates in
`.artifacts/20260908T004216702Z/`: 669 backend tests (334.25s), 26 tooling tests,
Ruff, frontend build/types, documentation/source-size checks, dependency audit (zero reported
vulnerabilities), readiness, migration 0031 and HTTP privacy. This run includes the cumulative
model-ledger accounting, case-limit acceptance and comparison-contract changes.

Both browser suites pass all 27 tests with unchanged assertions/timeouts: development stack
in 1.3m and compiled image in 45.0s. Compiled evidence is
`.artifacts/built-web-0dcf7b35833443d3a94cd2a789b1444d/`: production mode, UID 10001,
no Node/npm, successful migration and generated-container cleanup. Runtime review counts
2,735 main-stack and 1,843 compiled-image HTTP outcomes with no server/error outcomes.
The scoped counts are saved in runtime-review.json and image summary.json.

The existing Starlette/httpx warning remains. All processes completed. These browser suites
cover complete multilingual workflows; the new incompatible-comparison branch is verified
at the API level, not by a dedicated browser assertion. Local mocks do not prove real-provider
semantic quality, equivalent comparison inputs, crash recovery or hosted CI/release readiness.

## Evaluation comparison contract provenance
2026-09-08: two API regressions reproduced ordinary deltas for unknown/different score
contracts (`.artifacts/comparison-provenance-before.log`). New scores carry a contract marker;
the extracted comparison service requires matching known contracts per mode/language group.
Unknown, empty or mixed groups retain values but receive incomparable/null deltas.

Ruff and `uv run --frozen --extra dev pytest -q tests/test_evaluation*.py` pass all 98 tests
in 71.06s (`.artifacts/comparison-provenance-acceptance.log`), with PostgreSQL enabled in the
isolated Compose API test container and current app/tests mounted read-only. Mock providers
and an empty OpenAI key were used. Existing matching-contract and workspace-denial tests pass.
The Starlette/httpx warning remains. Source gate passes 176 files; the runner is 349 lines.
No UI change/browser rerun; existing direction/null rendering was inspected. Contract matching
does not establish identical datasets, prompts or providers. See
[provenance contract](evaluation-design.md#comparison-contract-provenance).

## Evaluation case prompt-token limits
2026-09-08: `.artifacts/case-token-limit-before.log` reproduced 16 failures: the scorer did
not accept measured usage, malformed limits were accepted, and all three modes lacked a
limit score. New `prompt_token_limit_match` checks inclusive acceptance, with null for no limit.
The loader rejects booleans, strings, fractions, negatives and database integer overflow.

Ruff and `uv run --frozen --extra dev pytest -q tests/test_evaluation*.py` pass 88 tests in
65.24s (`.artifacts/case-token-limit-verified.log`) in the isolated Compose API test container,
with current app/tests mounted read-only, PostgreSQL enabled and mock providers. The existing
Starlette/httpx warning remains. No frontend changes or browser rerun in this increment.
After adding three rejected-import regressions, Ruff and all 19 case-limit tests pass in
`.artifacts/case-token-limit-boundary.log` (4.68s). An invalid second case returns HTTP 400
with its line number and leaves evaluation runs/cases, AI calls and agents unchanged.
This verifies post-execution case acceptance, not spending admission or historical backfill.
See the [limit contract](evaluation-design.md#case-prompt-token-acceptance).

## Evaluation model-ledger accounting
2026-09-08: EN/JA/ZH API regressions reproduced prompt-token counts of 715/840/836 where
the scoped ledger recorded 611/738/734 (`.artifacts/evaluation-usage-before.log`, three failures).
System results now sum ledger prompt tokens and estimated model cost by workspace and graph.
New tests check actual persisted API results/metrics and exclude another workspace/run while
including recorded failed/cached usage and zero-call behavior.

Ruff and 24 focused tests pass in `.artifacts/evaluation-usage-final.log` (13.65s). The broader
`uv run --frozen --extra dev pytest -q tests/test_evaluation*.py` passes 72 tests (61.72s) in
`.artifacts/evaluation-usage-broader.log`, using the `asi-verification` Compose one-off API
container, current app/tests mounted read-only, `RUN_POSTGRES_TESTS=1`, mock embeddings and an
empty OpenAI API key. Documentation/source-size/whitespace checks pass; the evaluator remains
420 lines. The existing Starlette/httpx warning remains. No frontend changes were made or new
full browser run performed for this repair; the prior complete pipeline is recorded below.
Historical results, full embedding costs and case budget acceptance are outside this repair;
see the [accounting contract](evaluation-design.md#model-usage-accounting).

## Evaluation expectation coverage and full regression
2026-09-08: four failing regressions reproduced optional tool/guardrail metrics inflated by
untested cases. Scoring now persists expected lists and null untested scores; new aggregate
names use only evaluated cases. Historical metrics keep their original semantics. Ruff and
49 focused tests pass in `.artifacts/evaluation-coverage-verified.log`.

`./scripts/verify.ps1 -PythonExecutable 'C:/Users/ytxqf/AppData/Local/Programs/Python/Python312/python.exe'`
passes all 17 gates in `.artifacts/20260908T000709309Z/`: 639 backend tests (333.23s),
26 tooling tests, lint/build/types, documentation/source-size checks, dependency audit,
readiness, migration 0031 and HTTP privacy. Both browser suites pass 27 tests with unchanged
timeouts/assertions; EN/JA/ZH journeys verify measured tool rates and omitted untested guardrail
rates. Compiled-image evidence is `.artifacts/built-web-4b24b4723e0b4d3da93d8de20b7fbab5/`:
production mode, UID 10001, no Node/npm, successful migration and generated-container cleanup.

Runtime review records 2,521 main-stack and 1,821 compiled-image HTTP outcomes with no
server/error outcomes. The existing Starlette/httpx deprecation warning remains. This verifies
expectation inclusion and denominator handling, not semantic quality or unexpected-tool
exclusion. See the [metric contract](evaluation-design.md#optional-expectation-metrics) and
[completed plan](exec-plans/completed/evaluation-expectation-coverage.md).

## Cited duration support and full regression
2026-09-08: reproduced automatic finalization of EN/JA/ZH answers promising 700 days while
citing seven-day policies. `.artifacts/answer-duration-before.log` has seven failures and two
passes. Shared cited-text extraction and numeric-duration comparison now feed routing and final
unsupported-answer checks. Titles and uncited chunks cannot support invented quantities.
Focused Ruff/tests pass 108 cases with one PostgreSQL-only skip in
`.artifacts/answer-duration-verified.log`; the final full run includes PostgreSQL coverage.

`./scripts/verify.ps1 -PythonExecutable 'C:/Users/ytxqf/AppData/Local/Programs/Python/Python312/python.exe'`
passes all 17 gates in `.artifacts/20260907T234548644Z/`: 632 backend tests (334.38s), 26 tooling
tests, lint/build/types, documentation/source-size checks, zero-vulnerability dependency audit,
readiness, migration 0031 and HTTP privacy. Both browser suites pass 27 tests with ten workers
and unchanged assertions/timeouts. The compiled-image suite finishes in 39.5s in
`.artifacts/built-web-9d73604ad4174767bccc760623c9ada5/`; runtime identity is production,
UID 10001, no Node/npm. Migration and generated-container cleanup pass.

Runtime review finds 2,470 HTTP outcomes during the main run window and 1,787 in the separate
image window, with zero server/error outcomes in either. Summary files retain the scoped counts.
The existing Starlette/httpx deprecation warning remains. Quantity matching is not entailment:
relations, negation and other claim types remain unverified. See the
[duration contract](langgraph-workflow-design.md#numeric-duration-support) and
[completed plan](exec-plans/completed/answer-duration-support.md).

## Full regression after graph sequencing
2026-09-08: `./scripts/verify.ps1 -PythonExecutable
'C:/Users/ytxqf/AppData/Local/Programs/Python/Python312/python.exe'` passed all 17 gates in
`.artifacts/20260907T232714310Z/`. Results: 609 backend tests with PostgreSQL enabled (326.18s),
26 tooling tests, Ruff, documentation/source-size checks, frontend build/type checks, dependency
audit (zero vulnerabilities), readiness, migration 0031 and HTTP log-privacy probe.

Both full Chromium suites passed with ten workers and unchanged assertions/timeouts:
27 development-stack tests in 59.1s and 27 compiled-image tests in 39.6s. Compiled-image evidence
is `.artifacts/built-web-35f1da88c14846c79130279e2de2ab30/`: production mode, UID 10001,
no Node/npm, successful migrations and temporary-container cleanup. The captured API run window
has 2,505 HTTP outcomes and no server/error outcomes; the separate image window has 1,824 and
none. `runtime-review.json` and image `summary.json` preserve these scoped counts.

Strict standalone typing of the new Chromium diagnostic fixture also passed via
`npx tsc --ignoreConfig --noEmit --skipLibCheck --target ES2022 --module ESNext
--moduleResolution Bundler --strict tests/e2e/agent-network-fixture.ts` from frontend;
evidence: `.artifacts/agent-network-types-verified.log`. This separate check is not a runner gate.
The existing Starlette/httpx deprecation warning remains. No application code changed during
this verification turn. Hosted CI, real-provider quality and full operational recovery remain
unverified; the earlier editor stall was not reproduced or proven repaired.

## Agent summary transport diagnostics
2026-09-08: the editor test now uses `agent-network-fixture.ts` to attach Chromium transport
metadata for agent list/summary/workflow requests. It records endpoint categories, browser
request IDs, timestamps, statuses and terminal events; no URLs, headers, bodies or user content.
Assertions, route gating, concurrency and timeouts are unchanged. Tests that finish during
background loading can have pending requests at teardown; that alone is not a failure.

The instrumented built-web verifier passed all 27 browser tests in 41.2 seconds:
`.artifacts/built-web-087ce306cc784851a57751a258f1fd6e/`. The editor attachment has 78 events,
zero pending requests and zero failures. Runtime checks passed: production mode, UID 10001,
no Node/npm, 1,810 HTTP outcomes, zero server/error outcomes and successful container cleanup.

The earlier editor stall remains unexplained. Local Playwright 1.61.1 code asynchronously
updates interception after a one-use handler expires, but a synthetic loopback probe comparing
one-use and persistent handlers passed all 80 cases (`.artifacts/route-lifecycle-results.json`).
That does not confirm the suspected interception race or prove the intermittent issue repaired.
Retain both failed and successful runs. The subsequent full local pipeline passed as recorded above.

## Persisted graph step ordering
2026-09-08: backward/tied-clock regressions reproduced trace reversal and incorrect parent
selection (`.artifacts/graph-ordering-before.log`: two failures). New steps persist a positive,
per-run unique sequence under a workspace-scoped PostgreSQL run lock. Trace/latest-step/review
readers share ordering; legacy null sequences remain explicitly unknown. Migration 0031
preserves old rows and refuses rollback while sequenced history exists.

Ruff and 62 focused API/review/language/PostgreSQL tests pass in
`.artifacts/graph-ordering-verified.log`. Three migration compatibility tests pass in
`.artifacts/graph-ordering-migration-verified.log`; final additional legacy API and migrated
constraint coverage passes seven tests in `.artifacts/graph-ordering-final-tests.log`.
These suites overlap; do not sum them. The existing Starlette/httpx deprecation warning remains.
The isolated API was rebuilt and readiness passed (`.artifacts/graph-ordering-api-rebuild.log`).

The unchanged built-web suite in `.artifacts/built-web-f0e4f8b7074f47e7b7de7a5f0c9b7ca2/`
passes 26 tests, including the original requested-language/trace check, but fails the editor
test's agent-summary wait at line 213 after the 75-second test deadline. The saved network trace
shows that summary request pending without a response; its cause is unresolved. This is not a
green suite. Runtime inspection finds 1,715 HTTP outcomes and zero server/error outcomes;
the image uses production mode, UID 10001 and no Node/npm. Both temporary-container cleanups
succeeded. `review-summary.json` records this scoped inspection, not verifier success.
Preserve both failures; the full 17-gate pipeline and hosted CI remain unverified.

## Built web verification harness
2026-09-08: added `python scripts/verify_built_web.py` to the local runner and CI browser job.
It builds the image, runs explicit migrations, checks readiness/runtime identity, executes all
browser tests and inspects HTTP outcomes. Generated probe/migration containers are cleaned up
on failure; existing services/volumes remain intact. Twenty-six tooling tests and PowerShell
syntax validation pass, including runtime evidence rejection and simulated browser-failure cleanup.

The live run `.artifacts/built-web-68ed7c3cafd24484a4bdba5ed6a20833/` **failed**: build,
migration/startup/readiness/runtime configuration passed; browser result was 26 passed/1 failed
in 39.6s. Both cleanup commands returned zero. The language test remains unchanged. Its saved
trace shows detection/classification returned in the wrong execution order because get_trace
sorts wall-clock timestamps. See the [active repair](exec-plans/completed/graph-step-ordering.md).
The new normal local pipeline has 17 gates; neither the full runner nor hosted CI has verified
this addition green. Earlier successful manual built-image checks do not supersede this failure.

## Built web runtime
2026-09-08: `.artifacts/built-web/` records the optional compiled frontend/API image verification.
`backend.log` passes Ruff and **37 tests in 3.57s**: `test_frontend_static.py`,
`test_internal_error_response.py`, `test_request_logging.py`, `test_production_config.py`, using
`uv run --frozen --extra dev pytest -q` in the isolated mock API container. One existing
Starlette/httpx warning remains. Tests cover disabled serving, incomplete-build startup failure,
index caching, conditional assets, traversal/secret-path rejection and API 404/auth preservation.

`docker build -f infra/Dockerfile.web -t asi-verification-web .` compiles the browser with an
empty API base; the runtime contains only backend dependencies/assets, runs as UID 10001 and
has no Node/npm. A temporary container on `127.0.0.1:8001` joined the existing synthetic
verification database/network with mock providers and a generated temporary signing key.
`API_URL` and `FRONTEND_URL` both pointed at that origin. Full `npx.cmd playwright test
--project=chromium --reporter=line --trace=on --output=../.artifacts/built-web/browser` from
`frontend/` passed **27 tests in 41.2s**, ten workers, production mode explicitly selected.
Runtime review counted 1,861 HTTP outcomes with no server/errors.

The final Dockerfile makes production mode the default. `final-build.log` records rebuilding;
`missing-key.log` verifies startup rejects an absent non-default signing key. The final image
passed four `multilingual-browser.spec.ts` checks in 18.9s without an environment-mode override
(`final-browser.log`). Runtime/config/image evidence verifies UID 10001, production mode,
Node/npm absent, migration head 0030, and 430 HTTP outcomes without server/errors. This uses the
existing migrated database; it is not a fresh migration/recovery proof. Only the temporary
probe container was removed; verification data and existing services were preserved.

The [runbook](../infra/README.md#built-webapi-image) describes separate migration execution,
runtime settings and remaining TLS/secrets/operations work. Default Compose still uses Vite;
hosted CI does not yet verify this optional image. No production credentials or paid providers
were used, and no public endpoint was deployed.

## JSONL message type validation
2026-09-08: `.artifacts/jsonl-message-types/before.log` reproduces four accepted non-text
message values (object, array, number, boolean). The parser now requires a string before
trimming and language preparation; invalid values produce a typed import error with position
and no raw-value echo. Whole-batch validation prevents partial usable examples.

`after.log` passes Ruff and **40 affected tests in 14.81s**, one existing Starlette/httpx
warning. Command in the isolated mock container: `uv run --frozen --extra dev pytest -q
tests/test_jsonl_message_types.py tests/test_dataset_import_failure.py
tests/test_import_language_override.py tests/test_import_message_language.py
tests/test_datasets.py tests/test_csv_shape_validation.py`, after Ruff. New cases verify
failed batches, zero examples/messages and successful corrected numeric-string imports.

After rebuilding, `.artifacts/jsonl-message-types/live_probe.py` verifies four HTTP 400 errors
and a 201 numeric-string import with exact stored text (`live.log`). Synthetic user/workspace
data stays in the isolated verification stack. No browser rerun was needed for this parser-only
change; existing language detection and string trimming behavior remain unchanged.

## Strict CSV quoting validation
2026-09-08: `.artifacts/csv-quoting/before.log` records two failures: unterminated quotes and
trailing text after a closing quote were silently accepted (four existing/positive cases pass).
The CSV reader now uses strict dialect handling and translates `csv.Error` from header/row
reading into a typed `ImportParseError` with a line hint and no raw input text.

`after.log` passes Ruff and **36 affected tests in 12.27s**, one existing Starlette/httpx
warning. Command: `uv run --frozen --extra dev pytest -q tests/test_csv_shape_validation.py
tests/test_dataset_import_failure.py tests/test_import_language_override.py
tests/test_import_message_language.py tests/test_datasets.py`, after Ruff in the mock container.
Regressions require HTTP 400, failed batch, no partial examples and no private-text echo.
Valid quoted commas/newlines and doubled quote escapes retain their parsed content.

After rebuilding the API, `.artifacts/csv-quoting/live_probe.py` creates isolated synthetic
user/workspace data and verifies HTTP statuses 400/400/201 plus exact escaped-quote content
through the examples API (`live.log`). No browser rerun was needed for this parser-only change.
This enforces the configured standard-library CSV dialect, not every external CSV convention.

## Evaluation resource workspace isolation
2026-09-08: `.artifacts/evaluation-workspace-isolation/backend.log` passes Ruff and **28 affected
tests in 30.97s**, one existing Starlette/httpx warning. Command in the isolated mock container:
`uv run --frozen --extra dev pytest -q tests/test_evaluation_workspace_isolation.py
tests/test_evaluation_authorization_boundary.py tests/test_evaluations.py
tests/test_workflow_authorization.py`, after Ruff.

Two new cases exercise nine rejected requests in each workspace direction (18 total), using
a caller who owns both workspaces and real populated archived evaluations/folders. Detail,
both comparison operands, move, archive, permanent deletion, foreign-folder assignment/filter
and creation with a foreign folder return 404 without protected identifiers/content. Correctly
scoped detail and list requests succeed first. Evaluation/accounting/audit snapshots remain
unchanged after every rejection, and model dispatch is forbidden during the checks.

No application changes or browser rerun were needed. This verifies the named foreign-ID
boundaries; it does not establish complete permissions for every resource or concurrent
folder assignment/deletion behavior.

## Evaluation terminal failures
2026-09-08: `.artifacts/evaluation-terminal-failure/before.log` reproduces two unexpected
case/metric-publication failures leaving evaluation status running. `evaluation_execution.py`
now owns successful metric publication and rollback/failed-status recording on unexpected
errors. Original exceptions are re-raised and committed results/model accounting are retained.

`after.log` passes Ruff and **32 affected tests in 33.17s**, with PostgreSQL enabled and one
existing Starlette/httpx warning. Command: `uv run --frozen --extra dev pytest -q
tests/test_evaluation_terminal_failure.py tests/test_running_evaluation_deletion.py
tests/test_evaluation_audit_atomicity.py tests/test_evaluation_failure_usage.py
tests/test_evaluation_authorization_boundary.py tests/test_evaluations.py`, after Ruff in the
isolated mock container. Three new API cases cover post-case failure, metric flush failure,
and a second failure while persisting failed status. They verify original exception identity,
retained ledger/reservation usage, no partial metrics, and content-free correlated diagnostics.
When failure recording also fails, the run remains running and the log explicitly reports it.

Rebuilt API: `npx.cmd playwright test multilingual-browser.spec.ts --project=chromium
--reporter=line --trace=on --output=../.artifacts/evaluation-terminal-failure/browser` from
`frontend/` passes four checks in 30.4s. Captured logs contain 543 HTTP outcomes without
server/errors. The evaluator size limit was lowered to 479 lines. This is scoped verification;
the complete pipeline was not rerun. Process death, persistent storage outages and ambiguous
commit acknowledgments still need recovery design; no model replay or durable resume was added.

## Running evaluation deletion protection
2026-09-08: `.artifacts/running-evaluation-delete/before.log` reproduces two failures: API
permanent deletion returns 204 for a running evaluation, and PostgreSQL deletion succeeds while
real evaluation execution is paused after its model case with only consumed reservations.
The management service now rejects running-state deletion with `evaluation_running` (409).
Existing active-reservation conflicts keep precedence. Archive remains a visibility operation.

`verified.log` passes Ruff and **30 affected tests in 44.58s**, PostgreSQL enabled, with the
existing Starlette/httpx warning. It runs `tests/test_running_evaluation_deletion.py` plus the
five modules listed in the evaluation audit verification below, with `uv run --frozen --extra dev
pytest -q` in the isolated mock container. `after.log` retains the initial line-length failures.
The API case requires unchanged evaluation/accounting/audit snapshots after rejection. The
PostgreSQL case verifies consumed reservations, rejects deletion while paused, then releases
execution and checks completed status, results, metrics and successful subsequent deletion.

Rebuilt API verification: `npx.cmd playwright test multilingual-browser.spec.ts
--project=chromium --reporter=line --trace=on --output=../.artifacts/running-evaluation-delete/browser`
from `frontend/` passes four checks in 30.5s; 543 captured HTTP outcomes show no server/errors.
The evaluation route size limit was lowered to 322 lines. No provider call or test assertion
was bypassed. Stale-running recovery, cancellation and restart/resume remain unimplemented;
the complete backend/browser pipeline was not rerun for this scoped guard.

## Evaluation management audit atomicity
2026-09-08: `.artifacts/evaluation-audit/before.log` reproduces three API failures: audit errors
left moves/archives committed and permanent deletion removed evaluation children. Management
now delegates to `evaluation_management.py`, where mutation and actor-attributed audit share
one commit with rollback/re-raise. Routes no longer perform a second audit commit.

`verified.log` passes Ruff and **28 affected tests in 38.51s**, PostgreSQL enabled, one existing
Starlette/httpx warning. Command: `uv run --frozen --extra dev pytest -q
tests/test_evaluation_audit_atomicity.py tests/test_evaluation_authorization_boundary.py
tests/test_evaluations.py tests/test_evaluation_budget_concurrency.py
tests/test_evaluation_reservation_migration.py`, after Ruff in the isolated mock API container.
The initial line-length/import-order failures remain in `backend.log` and `backend-corrected.log`.

Three API regressions snapshot cases/runs/results/metrics, AI ledger, reservations and audits
after injected audit failure, then retry successfully. Three PostgreSQL cases use a separate
observer before audit commit, require unchanged visible rows after rollback and a usable session,
then verify exactly one actor/resource/action-correct audit on retry. Existing reservation
deletion and permission cases remain green. No migration or provider behavior changed.

After rebuilding the API, `npx.cmd playwright test multilingual-browser.spec.ts
--project=chromium --reporter=line --trace=on --output=../.artifacts/evaluation-audit/browser`
from `frontend/` passes all four checks in 30.8s. The captured runtime window has 543 HTTP
outcomes with zero server/errors. The evaluator shrank to 496 lines, routes to 328; both size
limits were lowered. Concurrent execution recovery, resource assignment races and ambiguous
commit acknowledgments remain outside this transaction guarantee. This is scoped verification,
not a rerun of the complete backend/browser pipeline.

## Evaluation management authorization
2026-09-08: `.artifacts/evaluation-authorization/backend.log` passes Ruff and **26 affected
tests in 26.45s**, with the existing Starlette/httpx warning. Command in the isolated mock API:
`uv run --frozen --extra dev pytest -q tests/test_evaluation_authorization_boundary.py
tests/test_workflow_authorization.py tests/test_evaluations.py`, following `ruff check .`.

Six new actor cases cover 26 denied list/detail/comparison/move/archive/permanent-delete
requests: anonymous 401, outsider 404, and disallowed reviewer/viewer/member/developer 403.
The fixture creates populated evaluations and an archived baseline through real APIs.
Allowed owner or viewer/member/developer reads succeed before denied operations are checked.
Pass-through service observers record no denied entry. Full row snapshots of cases, runs,
results, metrics, AI ledger, reservations and audits remain unchanged after each denial;
protected names and identifiers are absent from responses.

No application behavior changed; browser tests were not rerun for this API test addition.
Audit failure atomicity, archived-workspace policy and every foreign-resource-ID combination
remain separate boundaries. See the [completed plan](exec-plans/completed/evaluation-management-authorization.md).

## Full regression and refresh completion
2026-09-08: `./scripts/verify.ps1 -PythonExecutable
C:/Users/ytxqf/AppData/Local/Programs/Python/Python312/python.exe` passed **15 of 16 gates**
in `.artifacts/20260907T215215263Z/`. Backend: **572 passed in 297.16s**, PostgreSQL enabled,
one existing Starlette/httpx deprecation warning. Tooling: 22 passed. Startup/readiness,
migration 0030, Ruff, frontend types/build, dependency audit (zero vulnerabilities) and the
new HTTP privacy gate passed. Runtime review counted 2,507 HTTP outcomes with no server/errors.

Browser result: 26 passed, one notification failure. The preserved trace shows Refresh still
disabled and API requests pending when the eight-second toast assertion expired; completed
requests returned 200. The notification test now waits explicitly for Refresh to become enabled
within 30 seconds before asserting success text and the original 3,200/480ms fade timing.
The page clock remains paused during real network completion. No application change, added
retry, reduced worker count or weakened text/fade assertion was used. This test does not prove
a refresh latency target; startup overlap and refresh fan-out remain performance concerns.

`npx.cmd playwright test --project=chromium --reporter=line --trace=on
--output=../.artifacts/refresh-toast-completion/browser` then passed **all 27 tests in 59.3s**
from `frontend/`, using ten workers. Evidence: `.artifacts/refresh-toast-completion/browser.log`
and traces. The subsequent three-minute API log window contains 2,538 outcomes and no
server/errors (`runtime-summary.json`). The whole pipeline was not rerun after this test-only
change; the original failed run is retained. Real-provider quality and hosted CI remain open.

## Server exception log privacy
Saved implementation evidence inspected on 2026-09-08: `.artifacts/server-log-privacy/`.
`before.log` records three failures exposing private markers in ordinary, chained and grouped
Uvicorn exceptions. `backend-live-corrected.log` passes Ruff and **22 affected tests in 13.37s**,
with the existing Starlette/httpx deprecation warning. The earlier import-order lint failure
is retained in `backend-live.log`.

The command ran `uv run --frozen --extra dev ruff check .` followed by
`uv run --frozen --extra dev pytest -q tests/test_server_log_privacy.py
tests/test_internal_error_response.py tests/test_request_logging.py
tests/test_request_graph_correlation.py` in the isolated mock API container with current app
and tests mounted. The subprocess regression starts real Uvicorn with `app/logging.json`,
raises a synthetic error, verifies a 500 response/reference matching the HTTP outcome, and
checks retained exception type/location without the private marker. The exception event itself
does not contain that reference. `rebuild.log` and `access-probe.log` retain the API rebuild
and passing live access-log privacy probe.

These are saved scoped results, not an application rerun during this documentation audit or
a new complete pipeline result. Configuration/formatter ownership and exclusions live in
[observability](observability-design.md#server-exception-diagnostics). Global logger privacy,
retention and direct request correlation for exception diagnostics remain unverified.

## Runtime HTTP access-log privacy
2026-09-08: a synthetic path/query marker appeared in Uvicorn's duplicate access log despite
safe application logging (`.artifacts/http-log-privacy/before.log`). The new runtime check
reproduced the violation (`probe-before.log`). Container startup now uses `--no-access-log`.
After rebuilding the isolated mock API, `python scripts/check_http_log_privacy.py` passes
(`accepted.log`): one correlated structured 404 outcome, no raw marker in captured logs.

All **22 tooling tests** pass, including missing/duplicate outcome, unsafe secondary access log
and incorrect status regressions. PowerShell parser and documentation/whitespace checks pass.
The runtime gate is added to the local runner and browser CI job, bringing the normal local
run to 16 gates; the earlier full 15-gate result below predates this harness change. Neither
the whole pipeline nor hosted CI was rerun for this scoped runtime repair. Server exception
diagnostics are covered separately above; third-party loggers and retention remain open.

## CSV structural validation
2026-09-08: extra fields reproduced an unhandled parser exception; duplicate content headers
reproduced silently discarded text (`.artifacts/csv-shape/before.log`: two failures, one pass).
The parser now rejects duplicate headers and over-wide rows before examples are written.
Tests require typed API errors, no partial examples, a failed batch and valid quoted multiline CSV.

Ruff and `uv run --frozen --extra dev pytest -q tests/test_csv_shape_validation.py
tests/test_import_language_override.py tests/test_import_message_language.py
tests/test_dataset_import_failure.py tests/test_datasets.py` pass **33 tests in 12.17s**
(`backend.log`); one existing dependency warning remains. Rebuilt mock API and live synthetic
HTTP probe returned **400, 400, 201** for extra fields, duplicate headers and valid quoted
multiline content (`live.log`, `live_probe.py`). No browser rerun for this parser-only change.

## Declared dataset import language
2026-09-08: six API failures reproduced ignored language declarations in JSONL/CSV
(`.artifacts/import-language-override/before.log`). Optional per-conversation `language` now
accepts en/ja/zh and annotates the conversation and its messages. Tests cover kanji-only
Japanese and numeric conversations, content preservation, invalid values and malformed JSON
field types. Automatic detection remains available; invalid declarations reject the whole batch.

Ruff and `uv run --frozen --extra dev pytest -q tests/test_import_language_override.py
tests/test_import_message_language.py tests/test_dataset_import_failure.py tests/test_datasets.py
tests/test_dataset_authorization_boundary.py tests/test_resource_folders.py` pass **47 tests
in 19.31s** (`backend-corrected.log`). Initial test formatting failure is retained in
`backend.log`; one existing dependency warning remains. After mock API rebuild,
`npx.cmd playwright test multilingual-browser.spec.ts --project=chromium --reporter=line
--trace=on --output=../.artifacts/import-language-override/browser` passes **four checks in
29.1s**. Runtime: **543 HTTP outcomes, zero server/error outcomes**. This is caller annotation,
not translation or linguistic quality certification; mixed-language imports should use Auto.

## Neutral replies in imported conversations
2026-09-08: three API cases reproduced rejection of numeric/emoji replies within otherwise
detectable EN/JA/ZH conversations (`.artifacts/import-language/before.log`). The focused
`import_language.py` helper prepares all languages before persistence: nonempty messages with
no letters inherit their own conversation's detected language; alphabetic messages are detected
independently. Tests verify content preservation and numeric replies both before and after a
language-bearing message. No cross-conversation fallback is allowed.

Ruff and `uv run --frozen --extra dev pytest -q tests/test_import_message_language.py
tests/test_dataset_import_failure.py tests/test_datasets.py
tests/test_dataset_authorization_boundary.py tests/test_resource_folders.py` pass **35 tests
in 17.95s** (`backend.log`). The late-message failure case now uses unsupported alphabetic text;
standalone numeric CSV/JSONL cases still verify whole-batch failure without partial rows.
One existing dependency warning remains. After mock API rebuild, `npx.cmd playwright test
multilingual-browser.spec.ts --project=chromium --reporter=line --trace=on
--output=../.artifacts/import-language/browser` passes **four checks in 34.2s**. Runtime has
**543 HTTP outcomes with zero server/error outcomes**. This extends deterministic import
behavior, not language-model quality or explicit language override support.

## Concurrent human label edits
2026-09-08: two PostgreSQL tests reproduce first-insert uniqueness failure and stale-value
restoration failure (`.artifacts/label-concurrency/before.log`). Human edits now acquire a
workspace-scoped conversation NO KEY UPDATE lock before label lookup, then refresh an existing
label before update. Concurrent edits both succeed with one label ID; stale edits preserve
the requested value and actor. Imported labels remain distinct from human labels.

Ruff and `uv run --frozen --extra dev pytest -q tests/test_label_concurrency.py
tests/test_dataset_authorization_boundary.py tests/test_dataset_audit_atomicity.py
tests/test_dataset_import_failure.py tests/test_datasets.py tests/test_resource_folders.py`
pass **38 tests in 20.74s**, with PostgreSQL enabled (`backend.log`). One existing dependency
warning remains. After mock API rebuild, `npx.cmd playwright test multilingual-browser.spec.ts
--project=chromium --reporter=line --trace=on --output=../.artifacts/label-concurrency/browser`
passes **four checks in 32.6s**. Runtime: **543 HTTP outcomes, zero server/error outcomes**.
The API retains last-writer-wins semantics; this adds neither edit history nor conflict UI.

## Dataset authorization before service entry
2026-09-08: Ruff and `uv run --frozen --extra dev pytest -q
tests/test_dataset_authorization_boundary.py tests/test_datasets.py
tests/test_dataset_import_failure.py tests/test_resource_folders.py` pass **32 tests in 15.42s**
(`.artifacts/dataset-authorization/backend.log`), with one existing dependency warning.
Six actor cases exercise **25 denied requests**: anonymous 401, outsider 404, reviewer dataset
reads/writes 403, viewer writes 403, member move/delete 403 and developer delete 403.
Normal service observers never execute; dataset/batch/example/message/label/audit snapshots
remain unchanged after every rejection. Existing populated owner and permitted-role reads,
plus a human label before the denied replacement, prevent empty-fixture false confidence.
Existing successful import/label/management and cross-workspace tests pass too. Application
code did not change and browser tests were not rerun. This is scoped admission evidence, not
a complete role-by-route proof or concurrent label-editing guarantee.

## Dataset management audit atomicity
2026-09-08: two API failures reproduced dataset move/delete persisting despite failed audit
(`.artifacts/dataset-audit/before.log`). A focused service helper now commits both atomically;
routes pass the authenticated actor and retain permission checks. Failed deletion restores
dataset, batches, examples, messages and labels. Existing audit actions/metadata are preserved.

Ruff and `uv run --frozen --extra dev pytest -q tests/test_dataset_audit_atomicity.py
tests/test_dataset_import_failure.py tests/test_datasets.py tests/test_dataset_pagination_order.py
tests/test_resource_folders.py` pass **31 tests in 13.92s**, with PostgreSQL enabled
(`backend-corrected.log`). Separate observers see original rows before audit commit; failure
rolls back and retry adds one attributable audit. Initial formatting failure remains in
`backend.log`; one existing dependency warning remains.
After mock API rebuild, `npx.cmd playwright test multilingual-browser.spec.ts --project=chromium
--reporter=line --trace=on --output=../.artifacts/dataset-audit/browser` passes **four checks
in 30.9s**. Runtime: **543 HTTP outcomes, zero server/error outcomes**. Browser checks cover
integration; PostgreSQL tests establish transaction behavior. Concurrent editing and import/
label audit coverage are outside this repair.

## Dataset import validation atomicity
2026-09-08: three tests reproduced committed partial examples after late language-validation
failure in CSV, JSONL and a later message within one conversation
(`.artifacts/dataset-import-failure/before.log`). The importer now resolves all example/message
languages before inserting examples, messages or labels. A validation failure retains the
failed batch and empty dataset for diagnosis, without exposing a usable partial import.

Ruff and `uv run --frozen --extra dev pytest -q tests/test_dataset_import_failure.py
tests/test_datasets.py tests/test_dataset_pagination_order.py tests/test_resource_folders.py`
pass **27 tests in 11.29s** (`backend-corrected.log`). Regressions verify unchanged existing
rows, an empty failed dataset and successful corrected import. The initial test-line lint
failure is preserved in `backend.log`; one existing dependency warning remains.
After rebuilding the mock API, `npx.cmd playwright test multilingual-browser.spec.ts
--project=chromium --reporter=line --trace=on --output=../.artifacts/dataset-import-failure/browser`
passes **four checks in 30.8s**. Runtime has **543 HTTP outcomes with zero server/error outcomes**.
This scoped result postdates the complete runner below. It does not change language detection,
prove arbitrary database-failure recovery or repair dataset-management audit transactions.

## Complete regression after knowledge integrity repairs
2026-09-08: `./scripts/verify.ps1 -PythonExecutable
C:/Users/ytxqf/AppData/Local/Programs/Python/Python312/python.exe` passes **all 15 checks**
in `.artifacts/20260907T205147063Z/`. The run rebuilt the isolated stack with mock providers,
verified readiness and migration head 0030, and recorded worktree/revision and exact commands
in checks.json. No application code changed during execution; no retries were needed.

- **535 backend tests in 257.10s**, with PostgreSQL enabled; one existing Starlette/httpx warning.
- **27 Chromium browser tests in 1.0m**, using the existing ten workers and unchanged assertions.
- **19 tooling tests**, source-size (165 files), documentation and backend lint checks pass.
- Frontend build/type check and dependency audit pass; audit reports zero vulnerabilities.
- Captured runtime logs: **2,583 HTTP outcomes, zero server/error outcomes** (`runtime-summary.json`).

This combined run includes the recent correlation, client-error, permission, document audit
and concurrent-reindex changes. Earlier failure evidence remains preserved. The result proves
the exercised local contracts; it does not establish real-provider factual/semantic quality,
hosted CI, production workload/deadlines, durable crash recovery or deployment readiness.

## Concurrent knowledge reindexing
2026-09-08: controlled PostgreSQL overlap reproduced duplicate-version IntegrityError
(`.artifacts/knowledge-concurrency/before.log`). The first mock provider is paused; a second
session retains stale metadata and attempts reindexing. The test verifies real lock blocking
with pg_blocking_pids before releasing the first request. A scoped NO KEY UPDATE read with
populate_existing now serializes mutation/version allocation. Both requests succeed with
versions 2 and 3, distinct content and preserved newer title when the second omits title.

Ruff and `uv run --frozen --extra dev pytest -q tests/test_knowledge_concurrency.py
tests/test_knowledge_audit_atomicity.py tests/test_index_audit_accounting.py
tests/test_embedding_runtime.py tests/test_knowledge_authorization_boundary.py
tests/test_knowledge_documents.py tests/test_resource_folders.py` pass **46 tests in 27.90s**
with PostgreSQL enabled and mock/synthetic providers (`backend-corrected.log`). The earlier
test-formatting failure remains in `backend.log`; one existing dependency warning remains.
After API rebuild, `npx.cmd playwright test multilingual-browser.spec.ts --project=chromium
--reporter=line --trace=on --output=../.artifacts/knowledge-concurrency/browser` passes **four
checks in 29.3s**. Runtime logs contain **543 HTTP outcomes with zero server/error outcomes**.
This is controlled concurrency evidence, not a load benchmark or crash recovery drill.

## Knowledge indexing audit publication
2026-09-08: upload/reindex audit failure reproduced committed index changes in two tests
(`.artifacts/knowledge-audit/index-before.log`). The final success transaction now includes
the audit, with authenticated API actor attribution. Audit failure rolls back publication;
independently accounted provider usage survives. Explicit provider failures retain failed status.

Ruff and `uv run --frozen --extra dev pytest -q tests/test_knowledge_audit_atomicity.py
tests/test_index_audit_accounting.py tests/test_embedding_runtime.py
tests/test_knowledge_authorization_boundary.py tests/test_knowledge_documents.py
tests/test_resource_folders.py` pass **45 tests in 28.83s** with PostgreSQL enabled
(`index-backend-corrected.log`). Synthetic transport tests inspect publication from a separate
connection before audit commit, confirm rollback, retained successful usage, retry and actor
attribution. Provider-failure accounting and denied management checks also pass. One dependency
warning remains; the earlier lint failure is retained in `index-backend.log`.

After rebuilding the mock-provider API, `npx.cmd playwright test multilingual-browser.spec.ts
session-recovery.spec.ts --project=chromium --reporter=line --trace=on
--output=../.artifacts/knowledge-audit/index-browser` passes **12 checks in 35.1s**.
Runtime: **1,238 HTTP outcomes, zero server/error outcomes** (`index-runtime-summary.json`).
No paid provider calls. The [completed plan](exec-plans/completed/knowledge-audit-atomicity.md)
records scope; concurrent reindexing, process termination and ambiguous commits remain unproven.

## Knowledge move/delete audit atomicity
2026-09-08: two API failures reproduced the audit gap: a failed audit left a move committed or
deleted the document/index (`.artifacts/knowledge-audit/before.log`). The service now owns
actor-attributed audit publication in the same transaction. Failed persistence rolls back;
separate PostgreSQL observers see the original document/index before audit commit.

`uv run --frozen --extra dev ruff check .` and `uv run --frozen --extra dev pytest -q
tests/test_knowledge_audit_atomicity.py tests/test_knowledge_authorization_boundary.py
tests/test_knowledge_documents.py tests/test_resource_folders.py` pass **37 tests in 18.40s**
with PostgreSQL enabled and mock providers (`backend-corrected.log`). The initial test-line
lint failure remains in `backend.log`; one existing dependency warning remains.
After rebuilding the API, `npx.cmd playwright test multilingual-browser.spec.ts
--project=chromium --reporter=line --trace=on --output=../.artifacts/knowledge-audit/browser`
passes **four checks in 29.6s**. Runtime logs contain **543 HTTP outcomes, zero server/error
outcomes**. Browser checks cover refresh and full three-language journeys; atomicity is proven
by failure-injection/API and PostgreSQL tests, not inferred from those browser journeys.
Upload/reindex publication was repaired subsequently; see the indexing evidence above and
the [completed plan](exec-plans/completed/knowledge-audit-atomicity.md).

## Knowledge management authorization
2026-09-08: Ruff and `uv run --frozen --extra dev pytest -q
tests/test_knowledge_authorization_boundary.py tests/test_knowledge_documents.py
tests/test_folder_authorization_boundary.py` pass **38 tests in 16.93s** with mocked providers
and one existing dependency warning (`.artifacts/knowledge-authorization/backend.log`).
The six new actor cases exercise 19 denied writes through real authentication/membership:
anonymous 401, outsiders 404, viewer/reviewer writes 403, member move/delete 403 and developer
delete 403. Service observers remain empty after each denial, and full-row snapshots of
documents, versions, chunks, embeddings, AI runs and audits remain unchanged. Populated owner
and member reads prevent empty-fixture false confidence. Existing successful management and
foreign-workspace cases also pass. Application/UI behavior did not change; no browser rerun
was needed. This does not establish authorized-write atomicity or PostgreSQL concurrency.

## Client-visible error references
2026-09-08 documentation audit of saved evidence; application suites were not rerun for this
audit. `.artifacts/error-reference/before.log` records five failing reference/CORS regressions.
The subsequent `backend.log` records Ruff and **24 passing tests in 15.35s** from
`uv run --frozen --extra dev pytest -q tests/test_internal_error_response.py
tests/test_request_logging.py tests/test_request_graph_correlation.py
tests/test_workflow_authorization.py`, with mock providers and one existing dependency warning.
Tests cover generic 500 responses matching HTTP log IDs, configured/untrusted origins,
normal/handled CORS exposure and existing authorization/correlation behavior.

`frontend-build.log` records a successful build/type check. `browser.log` records **27 passing
Chromium tests in 57.7s**, using `npx.cmd playwright test --project=chromium --reporter=line
--trace=on --output=../.artifacts/error-reference/browser`. The new browser case injects a
500 response, verifies the displayed UUID, unchanged upload draft/session, then removes the
interception and verifies a real successful API retry. The browser injection does not itself
prove server error handling; the backend tests cover that boundary separately.

These are saved scoped backend and full browser results, not a new complete runner result.
Final implementation review added no-store and original-exception propagation regressions.
The same backend command with Ruff passes **25 tests in 16.20s** (`final-review-backend.log`).
Retained API logs contain **2,525 HTTP outcomes and zero server/error outcomes**
(`final-review-runtime.log`, `final-review-summary.json`); injected browser errors are not
server requests. No application code changed after the 27-test browser run.
The [completed execution record](exec-plans/completed/client-error-reference.md) records acceptance.
Global log sanitization, failures after response start, ambiguous commit
acknowledgments and automatic retry safety are not established by these checks.

## HTTP request-to-graph correlation
2026-09-08: HTTP middleware establishes a server-generated request context, propagated into
synchronous service workers and restored on normal/error exits. After GraphRun persistence,
`asi.workflow` emits only event/request_id/graph_run_id/trace_id. Direct service work outside
HTTP emits no fabricated request link. A failure after creation retains the correlation event;
that increment did not change graph failure/recovery behavior or add request headers to
unhandled server errors. The later client-visible error-reference work above covers the latter.

Backend lint and `uv run --frozen --extra dev pytest -q tests/test_request_graph_correlation.py
tests/test_request_logging.py tests/test_requested_language.py tests/test_review_publication.py`
pass **29 tests in 13.32s**, with PostgreSQL enabled and mock providers
(`.artifacts/request-graph/accepted-backend.log`). Coverage includes real API success/failure/
denial, two-case evaluation linkage, concurrent synchronous workers, context restoration and
absence of customer text, credentials and exception messages in the structured events.
One existing dependency warning remains. Earlier stages passed 25 tests with one PG skip,
then 28 with PostgreSQL enabled; logs are retained.

After rebuilding the API, `npx.cmd playwright test multilingual-browser.spec.ts
multilingual-workflow.spec.ts --project=chromium --reporter=line --trace=on` passes **seven
checks in 30.1s** (`browser.log`, `browser/`). API logs contain **591 HTTP outcomes with zero
server/error outcomes** and **18 graph events**. Every event joins an HTTP outcome and all
18 graph/trace pairs match a read-only PostgreSQL lookup (`correlation-summary.json`,
`graph-events.json`, `persisted-links.jsonl`). Repository gates pass over 163 source files.
No frontend/migration changes; the prior full runner predates this scoped increment.
Graphless calls, durable background propagation and global logger redaction remain open.

## Complete regression and refresh reliability
2026-09-08: `./scripts/verify.ps1 -PythonExecutable
C:/Users/ytxqf/AppData/Local/Programs/Python/Python312/python.exe` initially passed 14/15 gates
in `.artifacts/20260907T193400016Z`: 506 backend tests passed, but notification timing and
session-recovery injection failed (24/26 browser passes). Preserve that failed run.
The notification trace showed refresh reads pending; the session test could reject bootstrap
traffic before its intended Refresh click. It now arms rejection from the Refresh account read.

The catalog query reproduction (`.artifacts/refresh-reliability/query-before.log`) measured
150 queries. `guardrail_catalog_stats.py` now groups usage and ranks the newest eight failures
per type in workspace-scoped queries; the regression enforces at most six queries and exact
statistics/order with foreign-workspace fixtures. The service shrank from 457 to 389 lines.
Earlier fixture and lint mistakes remain in the same artifact directory; the corrected
focused guardrail/authorization suite passes 15 tests in 16.79s (`accepted-backend.log`).

The final complete run `.artifacts/20260907T195106290Z` passes **all 15 gates**:
**507 backend tests in 244.28s**, **26 browser checks in 1.1m**, 19 tooling tests, lint,
frontend build/types, zero frontend audit vulnerabilities, startup/readiness and migration
head 0030. PostgreSQL tests are enabled. Providers are mocked and credentials cleared.
Browser concurrency remains ten workers and notification timeouts/assertions are unchanged.
No application edits occurred during this final run; there were no retries.

Runtime summary: **2,519 HTTP outcomes, zero server/error outcomes**. Guardrail-read median
was 214.04 ms across 64 requests (maximum 1,234.38 ms), versus 1,170.31 ms across 60 reads
in the earlier failed run. These are observed suite timings, not a controlled load benchmark
or latency guarantee. Full traces/logs and checks.json retain attribution. Real-provider
quality, recovery and remaining release contracts are not established by this local run.

## Atomic folder mutation audit
2026-09-08: `.artifacts/folder-audit/before.log` reproduces create/rename/delete persisting
despite injected audit failure. Audit staging now belongs to ResourceFolderService, with one
commit and rollback/re-raise on persistence failure; route-level audit commits are removed.
Internal update/delete callers must supply actor identity. The service remains 282 lines.

With `RUN_POSTGRES_TESTS=1`, mock providers and current app/tests/alembic mounts, backend lint
and `uv run --frozen --extra dev pytest -q tests/test_folder_audit_atomicity.py
tests/test_folder_cycles.py tests/test_folder_cycle_concurrency.py tests/test_folder_patch.py
tests/test_folder_authorization_boundary.py tests/test_resource_folders.py` pass **43 tests
in 23.66s** (`final.log`). Three PostgreSQL audit cases observe unchanged state through a
separate connection after the folder flush, then inject audit failure and verify rollback
and exactly one audit on retry. Two existing PostgreSQL hierarchy cases also pass.
One existing dependency warning remains. The initial repaired run passed 40 tests (`after.log`).

After rebuilding the API, `npx.cmd playwright test folder-patch.spec.ts review-ux-smoke.spec.ts
restricted-role-security.spec.ts --project=chromium --reporter=line --trace=on` passes
**five checks in 34.7s** (`browser.log`, `browser/`). Runtime: **482 HTTP outcomes, zero
server/error outcomes**. Documentation/source-size/whitespace gates pass. No frontend or
migration change; full suites were not repeated for this scoped transaction repair.
These tests do not establish uncertain commit-acknowledgment recovery, external audit delivery
or serialization of resource assignment against folder deletion.

## Folder hierarchy cycle integrity
2026-09-08: `.artifacts/folder-cycles/before.log` reproduces four descendant-move API failures;
`concurrency-before.log` proves the old implementation admits both opposing PostgreSQL moves.
The service now serializes parent changes on the workspace, checks scoped ancestry and refreshes
cached target state. Direct/indirect descendant moves leave the tree unchanged; valid moves
remain possible. An additional stale-session test verifies restoring a former parent after a
competing move persists the requested value.

With `RUN_POSTGRES_TESTS=1`, mock providers and current app/tests/alembic mounts, backend lint
and `uv run --frozen --extra dev pytest -q tests/test_folder_cycles.py
tests/test_folder_cycle_concurrency.py tests/test_folder_patch.py
tests/test_folder_authorization_boundary.py tests/test_resource_folders.py` pass **37 tests
in 21.74s** (`final.log`), including two PostgreSQL cases. One existing dependency warning.
After rebuilding the API, `npx.cmd playwright test folder-patch.spec.ts
restricted-role-security.spec.ts --project=chromium --reporter=line --trace=on` passes
**three checks in 9.8s** (`browser.log`, `browser/`). Runtime records **235 HTTP outcomes,
zero server/error outcomes**. Documentation/source-size/whitespace gates pass. No frontend
code changed in this increment. Full application suites were not repeated; these checks do
not establish folder/audit atomicity, concurrent resource deletion/assignment or automatic
repair of pre-existing corrupt hierarchies.

## Folder PATCH preserves hierarchy
2026-09-08: reproduced four failures where a name-only PATCH detached a nested folder for
each resource type (`.artifacts/folder-patch/before.log`). The route now distinguishes an
omitted parent field from explicit null; the service preserves the parent unless requested.
The browser submits only the name on rename, avoiding an unnecessary cached-parent update.
`test_folder_patch.py` verifies rename and empty-patch preservation, explicit root movement,
and foreign-parent rejection without partially changing the name or parent.

Backend lint and `uv run --frozen --extra dev pytest -q tests/test_folder_patch.py
tests/test_folder_authorization_boundary.py tests/test_resource_folders.py
tests/test_workflow_authorization.py` pass **38 tests in 27.95s** (`after.log`), using mock
providers and current app/tests/alembic mounts. One existing dependency warning remains.
After rebuilding the API/frontend, `npx.cmd playwright test review-ux-smoke.spec.ts
restricted-role-security.spec.ts --project=chromium --reporter=line --trace=on` passes
**four checks in 33.7s**; `folder-patch.spec.ts` separately passes **one check in 4.2s** and
proves the browser request and persisted hierarchy. Logs/traces are in `browser/` and
`nested-browser/` under the same artifact directory. The three-minute API window records
**482 HTTP outcomes and zero server/error outcomes**. Frontend build/types, documentation,
source-size and whitespace gates pass. Full suites were not repeated for this scoped fix.
No migration was needed. Cycle prevention, concurrent folder changes and atomic audit
publication are not established by these API/browser regressions.

## Folder mutation authorization boundary
2026-09-08: `test_folder_authorization_boundary.py` adds 16 parameterized cases covering
knowledge-document, dataset, agent and evaluation folders for anonymous callers, outsiders,
viewers and reviewers. Each case proves owner-positive populated reads, then denied
create/rename/delete before service execution and unchanged folder/audit snapshots.
Observation wrappers preserve normal service behavior; authentication and permissions are real.

With current app/tests/alembic mounted and mock providers, backend lint and
`uv run --frozen --extra dev pytest -q tests/test_folder_authorization_boundary.py
tests/test_resource_folders.py tests/test_workflow_authorization.py` pass **34 tests in 26.50s**.
Evidence: `.artifacts/folder-authorization/backend.log`; one existing dependency warning.
Documentation/source-size/whitespace gates pass. No application defect was exposed or runtime
code changed. These SQLite API fixtures prove permission behavior, not concurrent transaction
semantics. Prior 474-test backend and 25-browser results predate this test-only addition;
application suites were not repeated beyond the affected boundaries. Full management-route
coverage, hierarchy integrity and transaction/audit atomicity remain separate requirements.

## Explicit support language
2026-09-08 documentation audit of saved evidence, not a new application test run:
`.artifacts/requested-language/backend-corrected.log` records backend lint and **83 passing
tests in 46.24s**, with one Starlette/httpx deprecation warning. The focused command was
`uv run --frozen --extra dev pytest -q tests/test_requested_language.py tests/test_agents.py
tests/test_answer_language.py tests/test_workflow_authorization.py tests/test_evaluations.py
tests/test_evaluation_rag_baseline.py tests/test_graph_budget_enforcement.py`, using mounted
current app/tests/migrations and mock providers. `frontend-build.log` records a successful build.

`browser.log` records **nine failures and 16 passes** from the 25-test Chromium run. Failures
include evaluation journeys, the new language-choice scenario and notification timing.
The corrected backend result does not supersede this failed browser run. Earlier failed
backend logs and browser traces remain under the same artifact directory. See the
[execution record](exec-plans/completed/explicit-support-language.md) for diagnoses and the next checks.
At that intermediate checkpoint the feature was not accepted. The continuation and final
acceptance evidence below supersede that status while preserving the failed run.

Implementation continuation: rebuilt the corrected mock/no-key API and fixed the browser
agent-creation matcher to compare the exact workspace pathname rather than the fixture host.
`npx.cmd playwright test --project=chromium --reporter=line --trace=on
--output=../.artifacts/requested-language/browser-corrected` passes **all 25 tests in 1.0m**
(`browser-corrected.log`). `frontend-build-final.log` records the fresh build/type check.
The five-minute corrected API log window records **2,291 HTTP outcomes, zero server/error
outcomes** (`runtime-corrected.log`, `runtime-summary.json`). The notification test passed
unchanged: its earlier trace shows a refresh guardrail request still pending at assertion
timeout. This pass does not establish a refresh latency guarantee or erase that failure.

Final full backend check: `docker compose -p asi-verification run --rm --no-deps` with
`RUN_POSTGRES_TESTS=1`, mock embeddings, an empty API key and current app/tests/alembic mounts
ran `uv run --frozen --extra dev ruff check . && uv run --frozen --extra dev pytest -q`.
`backend-full.log` records **474 passed in 272.31s**, including enabled PostgreSQL tests,
with one existing Starlette/httpx deprecation warning. All 19 tooling tests, documentation,
source-size (160 files) and whitespace checks pass. This completes language-choice acceptance;
real-provider linguistic quality and the earlier refresh latency concern remain unproven.

## Answer language excludes citation metadata
2026-09-08: shared answer-language detection excludes exact known chunk references before
checking prose. Japanese citation titles no longer reject English/Chinese answers or let English
and citation-only answers pass a Japanese check. Unknown references stay in the detected text;
guardrails also retain titles whose packed content is empty/malformed. Stored answers remain
unchanged. Mixed-language prose and kanji-only Japanese input remain heuristic limitations.

`.artifacts/answer-language/before.log` reproduces eight failures with four passes. The initial
fix passes 66 tests (`after.log`); after adding three malformed/empty evidence cases, full backend
lint and `uv run --frozen --extra dev pytest -q tests/test_answer_language.py
tests/test_answer_citations.py tests/test_guardrails.py tests/test_evaluation_score_contract.py
tests/test_evaluation_rag_baseline.py tests/test_evaluations.py` pass **69 tests in 19.56s**
(`final.log`), with the existing dependency warning. Current app/tests/alembic were mounted;
providers were mocked. Source-size/documentation/whitespace gates pass (158 application files).

The rebuilt mock/no-key API passed a live English workflow plus vector-RAG evaluation using a
Japanese-titled English policy; the citation title remains in the published answer and the
language score is 1 (`live-http.json`). `npx.cmd playwright test multilingual-browser.spec.ts
multilingual-workflow.spec.ts --project=chromium --reporter=line --trace=on
--output=../.artifacts/answer-language/browser` passes **seven tests in 32.0s**. Runtime review
records 598 HTTP outcomes and zero server/error-type failures in the three-minute window.
Full backend/browser suites were not repeated; this scoped evidence does not replace their
separately dated results or establish real-provider linguistic quality.

## Archived retrieval admission
2026-09-08: new retrieval search now requires an active workspace in addition to knowledge:read.
Owner/viewer/reviewer tests prove archive denial before RetrievalService entry and unchanged
workflow/AI/retrieval/evaluation counts; historical trace reads remain allowed, and restoring the
workspace enables search again. Existing role permissions are unchanged. Concurrent archival
cancellation of a request already admitted is not implemented by this check.

Evidence in `.artifacts/archive-admission/`: `before.log` showed protected execution but its
pytest.fail spy also caused AnyIO portal teardown errors. The non-throwing observation spy in
`reproduction.log` cleanly reproduces three HTTP 200-versus-409 failures. `verified.log` records
an import-order lint failure; after correction, `final.log` records full backend lint and
`uv run --frozen --extra dev pytest -q tests/test_archived_workflow_execution.py
tests/test_workflow_authorization.py tests/test_auth_workspace.py tests/test_retrieval.py
tests/test_retrieval_failures.py`: **45 passed, four PostgreSQL-only tests skipped, in 31.05s**.
One existing dependency warning remains; this scoped run used mock providers and SQLite fixtures.

After rebuilding the mock/no-key API, live HTTP archive denial (409), historical trace read
(200) and restored search (200) passed (`live-http.json`). `npx.cmd playwright test
restricted-role-security.spec.ts multilingual-browser.spec.ts multilingual-workflow.spec.ts
--project=chromium --reporter=line --trace=on --output=../.artifacts/archive-admission/browser`
passes **nine tests in 30.5s**. Runtime review shows 753 HTTP outcomes and zero server/error-type
failures in the three-minute window. Source-size/documentation/whitespace gates pass. Full
backend/browser suites were not repeated; prior full evidence remains separately dated below.

## Local loopback network boundary
2026-09-08: the local Compose profile now binds API, frontend, PostgreSQL and Redis host ports
to 127.0.0.1. Before the change, live Docker publishers showed wildcard IPv4 and IPv6 bindings.
`docker compose -p asi-verification config --format json` and subsequent live `ps --format json`
were checked for exactly four loopback bindings. Evidence in `.artifacts/loopback-network/`:
`config-bindings.json`, `live-bindings.json`, `startup.log`, `postgres-mounts.json`, `migration.log`.
The stack was recreated with `up -d --no-build`, mock embeddings and no provider key; PostgreSQL
retains the existing asi-verification_postgres_data volume and migration head 0030. API/frontend
HTTP readiness passed. This verifies Docker's publisher configuration, not an external network
penetration test or protection against local processes/other containers.

`npx.cmd playwright test --project=chromium --reporter=line --trace=on
--output=../.artifacts/loopback-network/browser` passes **24 tests in 57.1s**. Browser logs/traces
remain in that directory; runtime review reports 2,215 HTTP outcomes with zero server/error-type
failures in the three-minute window. Documentation and whitespace gates pass. Application
source was unchanged; the prior full 450-test backend/build/lint evidence remains applicable to
that source and was not rerun for four host-binding changes. Remote access requires an explicit
secured deployment profile; development credentials and production hardening remain open.

## Complete regression after citation and recovery work
2026-09-08: `./scripts/verify.ps1 -PythonExecutable
C:/Users/ytxqf/AppData/Local/Programs/Python/Python312/python.exe` passed all 15 checks in one
invocation. Evidence: `.artifacts/20260907T181501351Z/` (UTC artifact naming), including exact
commands/exit codes in `checks.json`, revision/worktree records, individual logs and browser
traces. No application source changed during this run.

Results: **450 backend tests in 222.60s**, **24 browser tests in 55.9s**, **19 tooling tests**,
CI-equivalent backend lint, frontend build/type checks, frontend dependency audit (zero reported
vulnerabilities), documentation/source-size checks, rebuilt stack readiness and migration head
0030_evaluation_reservations. All checks passed without a retry. One existing Starlette/httpx
deprecation warning remains. Full runtime log review recorded **2,222 HTTP outcomes, zero
server/error-type failures** in `runtime-review.json`. A live configuration read confirmed mock
embeddings and no provider key. The runner preserves caller environment settings.

This supersedes earlier full-suite counts for the current application state without deleting
prior failures or focused evidence. Restore drills are separate checks documented below, not
part of the 15-check runner. These results do not prove hosted CI, real-provider answer quality,
complete authorization coverage, load targets, network cutover or process-crash recovery.

## Restored application operation
2026-09-08: `python scripts/verify_database_restore.py` now starts a separate API container
against the disposable restored database after verifying its 36 public tables. Original journey
passwords authenticate for EN/JA/ZH; restored datasets/documents, graph/model traces, reviews,
evaluations and costs are readable. Anonymous and foreign-workspace reads are denied. A new
support run in each restored workspace completes with the expected seven-day fact, a citation
and two mock ledger calls. This uses FastAPI TestClient with real PostgreSQL dependencies and
no dependency overrides; it does not start a network listener or switch the browser endpoint.

Final artifact: `.artifacts/database-restore-54fa81d1030141ba9e205f4c1290105f/`.
`report.json` records all three language checks passing, migration 0030, unchanged source
fingerprints after the probe and successful target cleanup, in 28.703s. `application.log` and
`runtime-review.json` contain 33 HTTP outcomes with zero server/error-type failures. The normal
API remained healthy. The earlier attempt in `database-restore-5436bf207c1e4ea1944abdfcbe18bf22`
failed because the probe expected an items wrapper on the list-valued evaluations response;
its evidence was retained and target cleaned before the corrected run.

All 19 tooling tests pass, including cleanup/reporting after an application-probe failure.
Documentation/source-size/whitespace gates pass. No application source changes or full-suite
rerun. Network/browser cutover, process crash recovery, external backup operations and RPO/RTO
remain separate unverified requirements.

## Local database restore
2026-09-08: `python scripts/verify_database_restore.py` passed in 9.735s against the synthetic
asi-verification PostgreSQL stack. Evidence:
`.artifacts/database-restore-2083e3d4843e4d52b4631ccdddf50557/report.json` and `database.dump`
(2,461,731 bytes). All 36 public tables matched source/restore row counts and ordered JSON
fingerprints; source manifests were unchanged before/after the dump and restore. This includes
518 workspaces, 587 graph runs, 830 retrieval traces, 245 human reviews, 569 evaluation results,
1,309 AI ledger records and 311 document chunks. Restored migration: 0030_evaluation_reservations.
pg_restore used exit-on-error and one transaction. Cleanup was independently confirmed by
pg_database returning zero matches for the generated target; the source API remained healthy.

`python -m unittest discover -s scripts/tests -q` passes 19 tests. The new tests cover successful
cleanup, dump/create/restore failure, changed source, mismatched restored content and cleanup
failure reporting. Documentation, source-size and whitespace checks pass. Application code was
unchanged and its suites were not rerun. This does not establish restored-application cutover,
external backups, scheduled retention, disaster recovery, or RPO/RTO; follow the
[local restore runbook](../infra/README.md#local-logical-backuprestore-drill).

## Human review answer integrity
2026-09-08: approval/edit now validate nonblank content and canonical references against the
workspace/run's latest successful packed-evidence snapshot before changing review state. A failed
latest step is not accepted. Uncited human responses and rejection remain available. Missing,
malformed, foreign-workspace or mixed invented references return an explicit 400; the pending
review can be corrected without partial run/checkpoint/audit publication.

`.artifacts/review-answer-integrity/before.log` reproduces five failures with five passes.
`after.log` records the initial 42 passing tests. Import-order and later test-line-length lint
failures remain in `lint.log` and `verified.log`. Final `ruff check .` and `uv run --frozen
--extra dev pytest -q tests/test_review_answer_integrity.py tests/test_human_reviews.py
tests/test_review_transactions.py tests/test_review_publication.py
tests/test_workflow_authorization.py` pass **48 tests in 33.13s** (`final.log`), using mounted
current app/tests/alembic and `RUN_POSTGRES_TESTS=1`. Existing PostgreSQL concurrency/rollback
regressions pass; the new request-validation cases use SQLite. One dependency warning remains.

After rebuilding the mock/no-key API, `npx.cmd playwright test review-ux-smoke.spec.ts
restricted-role-security.spec.ts multilingual-browser.spec.ts multilingual-workflow.spec.ts
--project=chromium --reporter=line --trace=on
--output=../.artifacts/review-answer-integrity/browser` passes **11 tests in 40.5s**. Logs and
traces remain in that artifact directory; runtime review shows 990 HTTP outcomes and zero
server/error-type failures in the two-minute window. Documentation/source-size/whitespace
gates pass. The service shrank from 316 to 312 lines and its legacy baseline was lowered.
No full backend/browser suite rerun, schema migration or paid provider call was needed.
Reference integrity does not prove factual support, current-policy validity or complete security.

## Evaluation citation integrity
2026-09-08: the vector-RAG baseline now reuses the agent answer-reference validator. A generated
candidate containing both a valid packed-source citation and an invented chunk reference no
longer finalizes or receives accepted citations. Candidate text and ledger usage remain visible
for evaluation inspection. This does not establish factual support or create a review queue item.

`.artifacts/evaluation-citations/before.log` reproduces one mixed-reference failure with 11 passes.
With current app/tests/alembic mounted, `uv run --frozen --extra dev pytest -q
 tests/test_answer_citations.py tests/test_evaluation_rag_baseline.py
 tests/test_evaluation_failure_usage.py tests/test_evaluation_budget_admission.py
 tests/test_evaluation_score_contract.py tests/test_evaluations.py` passes **58 tests in 22.77s**
(`after.log`). Valid, repeated, missing, altered, empty and mixed references are covered;
usage remains recorded on rejected candidates. The existing dependency warning remains.
`ruff check .` passes (`lint.log`); documentation, source-size and whitespace gates pass.

After rebuilding the mock/no-key API, `npx.cmd playwright test multilingual-browser.spec.ts
multilingual-workflow.spec.ts --project=chromium --reporter=line --trace=on
--output=../.artifacts/evaluation-citations/browser` passes **7 tests in 30.7s**. Browser traces
and logs remain in that artifact directory. Runtime review records 591 HTTP outcomes and zero
server/error-type failures in the two-minute window. Full backend/browser suites were not rerun;
these focused checks do not replace their separately dated evidence below.

## Evaluation failure usage
2026-09-08: evaluation results now copy prompt tokens and estimated cost from a ModelProviderError's
attached ledger instead of retaining the input-question estimate and zero cost. Provider overrun
still produces an error result with no answer and a failed case; its recorded usage contributes
to grouped metrics. This does not reconcile unknown external billing or invent missing usage.

With app/tests/alembic mounted from the worktree, `uv run --frozen --extra dev pytest -q
tests/test_evaluation_failure_usage.py tests/test_evaluation_budget_admission.py
tests/test_evaluation_provider_routing.py tests/test_evaluation_rag_baseline.py
tests/test_evaluations.py tests/test_evaluation_score_contract.py` passes **36 tests in 18.60s**.
The tests use synthetic provider transport; no real model calls occur. The existing dependency
deprecation warning remains. `ruff check .`, documentation/size/whitespace checks pass.

The initial fixture forgot to invalidate cached settings and failed before provider dispatch;
those logs remain in `.artifacts/evaluation-failure-usage/before.log` and `after.log`.
After correction, `reproduction.log` ran against the confirmed pre-fix API image and showed
5 reported prompt tokens versus 4,000 ledger tokens in both baseline modes. `verified.log`
contains the final passing tests, including cost/metric agreement and preserved answer rejection.

After rebuilding the mock/no-key API, `npx.cmd playwright test multilingual-browser.spec.ts
multilingual-workflow.spec.ts --project=chromium --reporter=line --trace=on
--output=../.artifacts/evaluation-failure-usage/browser` passes **7 tests in 31.3s**.
`browser.log`, `browser/`, `runtime.log` and `runtime-review.json` retain evidence: 591 HTTP
outcomes with zero server/error-type failures in the two-minute runtime window. The full backend
and full browser suites were not repeated for this focused reporting change; prior results below
remain separately dated. No schema or frontend application changes were required.

## Evaluation baseline budget admission
2026-09-08: the disposable API test container ran `uv run --frozen --extra dev pytest -q` with
`RUN_POSTGRES_TESTS=1`, mock embeddings and no provider key: **427 passed in 269.07s**, with the
existing Starlette/httpx deprecation warning. App/tests/alembic were mounted from the worktree.
Focused provider checks passed 25 tests; focused PostgreSQL budget/migration checks passed 25.
The full suite includes all final cases, including cumulative baseline usage and deletion refusal.
`ruff check .` passes across mounted application, tests and migrations after formatting fixes.

The new checks cover direct/vector token/cost denial before provider dispatch, cumulative
baseline usage, active-reservation deletion refusal, evaluation-versus-graph monthly contention,
and no workspace lock held during a paused provider call. Migration tests preserve existing
graph reservations, allow safe rollback, and refuse rollback with evaluation reservation history.
The isolated live API is on `0030_evaluation_reservations`; mock/no-key settings were verified.

From `frontend`, `npx.cmd playwright test --project=chromium --reporter=line --trace=on
--output=../.artifacts/evaluation-budget/browser-final` passes all **24 tests in 55.5s**.
The first run passed 23 tests but the toast fixture clicked Refresh before workspace bootstrap
was guaranteed complete. Its trace was retained; the test now awaits the workspace title and
permitted navigation before testing dismissal timing. Assertions and application behavior were
not weakened. No frontend application change or frontend build was needed for that fixture repair.

Evidence under `.artifacts/evaluation-budget/`: `before.log` shows both baseline bypasses;
`focused.log`, `postgres.log`, `backend-full.log`, `lint-corrected.log`, `browser-final.log` and
`browser-final/` retain successful checks. Earlier lint and browser failures remain separately
saved. `runtime-final.log`/`runtime-final-review.json` record 2,222 API outcomes and zero server
failures over the final two-minute window. All 17 tooling tests and documentation/source-size
(156 application files)/whitespace gates pass. This was not a new invocation of the full
15-check runner. See [token economy](token-economy-design.md) for remaining accounting limits.

## Restricted-role browser verification
2026-09-08: from `frontend`, `npx.cmd playwright test --project=chromium --reporter=line --trace=on
--output=../.artifacts/restricted-roles/final` passes all 24 tests in 55.1s. Two new real
viewer/reviewer journeys use actual registrations, memberships, PostgreSQL resources and HTTP
responses; no permission responses are mocked. They verify allowed knowledge/retrieval with
citations, foreign document filtering, 404 for foreign workspace reads/search, and 403 for
forged indexing, deletion, agent runs, evaluations and membership escalation. Viewer resolution
is denied; a reviewer rejects through UI controls and the owner observes the persisted failed run.
Denied requests leave AI/graph totals, token/cost totals and the document list unchanged.
Both journeys assert retained login sessions and no browser exceptions.

In the disposable API container with app/tests mounted read-only and mock providers,
`uv run --frozen --extra dev pytest -q tests/test_workflow_authorization.py` passes seven tests
in 13.88s. These use SQLite fixtures and spies that fail if denied requests enter retrieval,
graph or evaluation execution, plus ledger counts. They complement the PostgreSQL browser
evidence; unchanged cost alone is not proof that a provider was never invoked.

`.artifacts/restricted-roles/focused.log` retains one selector failure (viewer control is labeled
Read only) and one reviewer pass. `final.log`, `final/` and `backend.log` retain final results.
`runtime.log`/`runtime-review.json` record 2,376 API outcomes with zero server/error-type failures
over a three-minute window. Mock embeddings and no provider key were verified. The existing
Starlette/httpx deprecation warning remains. Documentation/size/whitespace checks pass; no
application source changed, so builds and the full backend suite were not repeated.
This is targeted role coverage, not a complete route/resource-management or concurrency proof.

## Session recovery
2026-09-08: `npm.cmd --prefix frontend run build` passes. From `frontend`,
`npx.cmd playwright test --project=chromium --reporter=line --trace=on
--output=../.artifacts/session-recovery/final` passes all 22 tests in 51.1s.
Seven new cases cover invalid saved credentials, bootstrap 503/network failures and manual retry,
protected 401 versus 403, a delayed old-session 401, and wrong-password/corrected-password login.
Invalid saved credentials and wrong-password rejection use the real API. Transient failures and
mid-session 401/403 use controlled browser responses; surrounding auth/workspace requests are live.
Each new case checks for uncaught browser exceptions. 403 preserves drafts/session; 401 clears
scoped state and permits sign-in. No paid providers or automatic mutation retries were used.

Preserved `.artifacts/session-recovery/` evidence: `before.log` and trace show invalid-token
startup failing to return to login. `focused.log` shows four passes and the disabled Refresh
failure before its repair. `final.log` and `final/` contain all successful tests and traces.
`runtime.log` and `runtime-review.json` cover a four-minute API window with 2,506 HTTP outcomes
and zero server/error-type failures. Mock embeddings and absence of a provider key were checked.
All 17 tooling tests, documentation/source-size gates (155 application files) and diff whitespace
checks pass. No backend source changed and the backend suite was not rerun for this frontend repair.
The [completed plan](exec-plans/completed/session-recovery.md) records decisions and remaining scope.

## Workspace response isolation
2026-09-08: `npm.cmd --prefix frontend run build` passes type checking and production build.
From `frontend`, `npx.cmd playwright test --project=chromium --reporter=line --trace=on
--output=../.artifacts/workspace-isolation/final` passes all 15 tests in 49.4 seconds.
`workspace-response-isolation.spec.ts` covers delayed document responses after workspace switch,
logout/login as a separate user, and an old workspace-creation callback after A-to-B-to-A.
It verifies draft reset and no browser exceptions. The fixture holds actual API responses;
500ms settling windows allow competing initial loads and delivered React updates to finish.

Evidence in `.artifacts/workspace-isolation/`: `reproduction.log` and its trace show A's private
title replacing B's list before the repair. `before.log` was an initially premature observation,
not proof of isolation. `after.log` records 13 passing tests and an ambiguous Login-selector
failure; `focused.log` passes all three after correcting the selector. `final.log` and `final/`
retain the complete successful run and traces. `runtime.log` contains a five-minute API window
covering focused/final verification: 3,529 HTTP outcomes, zero status-5xx/error-type matches.
The live API used mock embeddings and no provider key. No paid model calls were made.

Documentation and source-size gates (154 application files), all 17 tooling tests, and
`git diff --check` pass. No backend source changed; backend tests were not rerun for this repair.
The [completed plan](exec-plans/completed/workspace-response-isolation.md) owns decisions.
This validates UI lifetime isolation, not backend cancellation or complete permission coverage.

## Complete local verification runner
2026-09-08 (JST): `scripts/verify.ps1 -PythonExecutable
C:/Users/ytxqf/AppData/Local/Programs/Python/Python312/python.exe` passes all 15 checks in
`.artifacts/20260907T162849956Z/checks.json` (artifact names use UTC). Results include 17 tooling
tests, 415 backend tests in 211.11 seconds, 12 Chromium tests in 42.2 seconds, startup/readiness,
migration head 0029, backend lint including migrations, frontend install/build, browser install,
npm audit and runtime-log capture. Npm audit reports zero vulnerabilities; the existing
Starlette/httpx deprecation warning remains. Browser traces are retained for every test.

The wrapper set parent EMBEDDING_PROVIDER=openai before invoking the runner. Live inspection
confirmed mock embeddings and no provider key inside the API; the wrapper verified that the
parent provider setting was restored afterward. The runner now explicitly selects mock
embeddings, runs CI-equivalent `ruff check .` before tests and captures runtime logs quietly.
`runtime-review.json` records manual inspection of 790 application HTTP outcome records:
zero status >=500 or non-null error_type records. Log capture alone is not an error-free gate.

Earlier full runs `.artifacts/20260907T161722518Z/` and `.artifacts/20260907T162255221Z/`
completed with one failing check: import grouping in migration 0029, previously excluded by
the runner's narrower lint command. The first repair changed ordering but missed a required
blank line. Ruff's exact diff and a passing lint preflight preceded the successful full rerun.
Preserve both failed runs. This establishes local harness execution, not hosted CI, recovery
targets, real semantic quality, complete permission coverage or production certification.

## Failed retrieval trace persistence
2026-09-08: `.artifacts/20260908-retrieval-failures/full.log` passes 414 backend tests with
PostgreSQL enabled in 235.92 seconds. `final-focused.log` passes 13 tests in 17.62 seconds after
adding the successful-empty-search case and final failed graph-step trace-ID assertions. Do not
describe this as a 415-test full run. One existing Starlette/httpx deprecation warning remains.
The initial focused run passed 18 tests but failed on a detached ORM object in the new migration
fixture; retaining the workspace ID inside its session corrected that fixture. The full run
verifies legacy outcome backfill, safe downgrade/re-upgrade and refusal to erase failed evidence.

Failure cases use synthetic configured embeddings: provider error, malformed response and stored
vector corruption. Failed direct requests return a trace ID; a new session reads the persisted
failed outcome with no retrieved chunks. Anonymous and foreign-workspace reads fail. Empty
searches succeed with no source; failed graph steps retain trace IDs and graph-owned persistence.
Failures before language validation/trace creation and database outages are not covered by this
persistence guarantee. Trace query text remains protected data, not general logging material.

`browser.log` passes all 12 Chromium tests in 40.7 seconds against the rebuilt mock API.
The running database reports `0029_retrieval_outcome (head)`. `lint-verified.log` passes backend
Ruff; documentation/source-size (153 files) and whitespace checks pass. Commands use the mounted
Compose pytest/Ruff invocation below, with `RUN_POSTGRES_TESTS=1`; focused files are
`tests/test_retrieval_failures.py tests/test_graph_embeddings.py`. Browser invocation is
`npx playwright test --project=chromium --reporter=line`. No paid calls were made.

## Mixed valid and invented citations
2026-09-08: `.artifacts/20260908-citation-integrity/before.log` reproduces four unit cases where
one valid citation masks an additional unknown, malformed, wrong-version or wrong-index marker.
The same run's three multilingual fixture failures were caused by exceeding reserved mock
completion usage, not proof of a citation-routing defect. `after.log` fixed the validator but
still exposed those fixture failures. Shortening the injected answer while preserving a known
citation plus invented reference isolates the intended behavior. Tests now require successful
model ledger records as well as review routing, a retained proposal and no final answer.
`full.log` passes all 411 backend tests with PostgreSQL checks enabled in 222.02 seconds,
with one existing Starlette/httpx deprecation warning.

`corrected.log` passes 36 affected tests in 9.56 seconds; one PostgreSQL-only publication test
was skipped there. `browser.log` passes all 12 Chromium tests in 36.2 seconds on the rebuilt mock
API; `api.log` contains no HTTP 5xx records. `lint-final.log` passes after shortening one
overlong guardrail message. Documentation, source-size (152 files) and whitespace checks pass.
The shared validator enforces exact packed citations and rejects leftover canonical chunk
markers. It does not prove factual entailment or recognize every invented prose reference.

Commands use the mounted mock Compose invocation below. Focused pytest files are
`tests/test_answer_citations.py tests/test_review_publication.py tests/test_mock_support_answer.py`;
full verification sets `RUN_POSTGRES_TESTS=1`. Browser command is
`npx playwright test --project=chromium --reporter=line`. No paid provider calls were made.

## Concurrent first-use budget policy creation
2026-09-08: inspection of the earlier reconciliation screenshot's fetch-error incident found
GET budget-policy request `21548eed-34ef-45cf-b2cf-104d7c345bb6` failed with HTTP 500 and an
IntegrityError on the unique workspace budget-policy constraint. Raw synthetic API logs are
preserved in `.artifacts/20260908-fetch-diagnosis/api.log`. Both synchronized PostgreSQL
regressions in `before.log` reproduce duplicate insertion: policy/policy and policy/embedding.
The service now acquires the admission-compatible workspace lock after a missing read, rechecks
the policy and releases the initialization lock at commit. `after.log` passes all 11 focused
concurrency/accounting tests in 11.25 seconds; `lint.log` passes backend Ruff.
`full.log` passes all 402 backend tests in 219.55 seconds with one existing Starlette/httpx
deprecation warning. Documentation/source-size (152 files) and whitespace checks pass.

`browser.log` passes all 12 Chromium tests in 40.3 seconds against the rebuilt mock API.
`live-race.json` records 24 successful authenticated first-use reads (eight simultaneous Costs
and Budget Policy reads on each of three fresh synthetic workspaces). `api-after.log` contains
no HTTP 5xx records after rebuild during browser/probe verification. This diagnoses and repairs
the observed database failure; it does not establish that every future network error is fixed.
Commands use the same mounted Compose pytest/Ruff invocation described below, with focused
files `tests/test_budget_policy_concurrency.py`, `tests/test_embedding_attempts.py` and
`tests/test_embedding_reconciliation_transactions.py`. Browser command is
`npx playwright test --project=chromium --reporter=line`. Failed and passing evidence is retained.

## Embedding reconciliation operator UI
2026-09-08: `.artifacts/20260908-reconciliation-ui/full-browser.log` passes all 12 Chromium
tests in 37.9 seconds. New tests exercise bounded pagination, pending-call protection, owner
confirmation, read-only controls, list recovery and draft retention after rejected submission.
Embedding responses and read-only membership presentation are simulated; surrounding auth,
workspace and Costs requests use the live isolated API. Backend permission and atomicity proof
remains in the reconciliation API tests below; this is not a real billing exercise.

The initial `browser.log` failed on the incorrect Costs navigation label. `verified.log` caught
a one-shot failure fixture consumed by StrictMode's repeated mount effect. Keeping the simulated
outage active until explicit recovery repaired the fixture. Failed screenshots/traces remain.
Screenshot inspection of the passing full run found a shell `Failed to fetch` toast outside the
panel. Its cause was unresolved at that checkpoint; the later budget initialization investigation
above found and repaired a matching server-side uniqueness failure. Added request-failure
assertions; `diagnostic.log` passes both
focused tests in 6.4 seconds without failed requests. Do not treat this rerun as a diagnosis.

Commands: from frontend, `npx playwright test --project=chromium --reporter=line` with artifact
output paths; diagnostic run adds `tests/e2e/embedding-reconciliation.spec.ts`. `npm --prefix
frontend run build` passes in `build.log`; mock-stack frontend rebuild is in `rebuild.log`.
Source-size gate passes over 152 files with the shell still at 8,067 lines. No backend source
changed in this increment. Pending-attempt crash recovery and real-provider verification remain.

## Embedding usage reconciliation API
2026-09-08: `.artifacts/20260908-embedding-reconciliation/full.log` reports 399 backend tests
passing in 216.20 seconds, including PostgreSQL checks. After adding the budget-release regression,
`focused.log` reports all 22 reconciliation tests passing in 11.65 seconds. The full suite was
collected before that last test; do not describe this as a 400-test full run. Both retain one
existing Starlette/httpx deprecation warning. `lint-final.log` passes backend Ruff; initial lint
found three overlong lines, corrected before final verification.

Commands use `docker compose -p asi-verification run --rm --no-deps` with read-only backend
app/tests/alembic mounts at `/app/`, `-e RUN_POSTGRES_TESTS=1 -e EMBEDDING_PROVIDER=mock
-e OPENAI_API_KEY=`, and `api uv run --frozen --extra dev pytest -q`. The focused run appends
`tests/test_embedding_reconciliation.py tests/test_embedding_reconciliation_transactions.py`.
Lint uses `api uv run --frozen --extra dev ruff check app tests` with app/tests mounts.
Coverage includes owner/denied-role/foreign/archived boundaries, strict input validation,
pending protection, repeated and competing updates, stale ORM refresh, audit-failure rollback,
original pricing and the effect of confirmed usage on subsequent budget admission.

`rebuild.log` records the isolated mock API rebuild. Live checks confirmed API/frontend HTTP
readiness, OpenAPI route registration and anonymous list rejection (401). No paid calls were
made. This is API recovery evidence, not an operator UI or real billing reconciliation exercise.
Documentation/source-size (149 files) and whitespace checks pass.

## Graph embedding admission and tracing
2026-09-08: `.artifacts/20260908-graph-embeddings/tests.log` records extraction regressions caused
by removing a helper import still used in drafting/context packing. Restoring it produces 43
affected passes in `after.log`. Added PostgreSQL checks cover agent/per-run token/cost admission,
foreign graph IDs, pending allowance, runtime run/step links and failure-to-review routing.
`full.log` passes all 378 backend tests in 209.25 seconds. The full command uses read-only
app/tests/alembic mounts at `/app/` and `docker compose -p asi-verification run --rm --no-deps
-e RUN_POSTGRES_TESTS=1 -e EMBEDDING_PROVIDER=mock -e OPENAI_API_KEY= api uv run --frozen --extra dev
pytest -q`. Configured-provider tests substitute synthetic transport; no paid calls were made.
`lint-verified.log` passes Ruff after the recorded import/formatting failures. `rebuild.log`
records the isolated mock-mode API rebuild; `browser.log` passes ten Chromium tests in 31 seconds
using `npx playwright test --project=chromium --reporter=line`. Documentation, source-size (146
files, 23 exceptions), and whitespace checks pass. One existing Starlette/httpx warning remains.
This verifies graph attribution/admission and default browser behavior, not real semantic quality.

## Configured embedding runtime
2026-09-08 completion: `.artifacts/20260907-embedding-runtime/tests.log` records 45 affected tests
passing; `full.log` records all 369 backend tests passing in 193.42 seconds after batch and failure
coverage was added. PostgreSQL API integration checks EN/JA/ZH configured indexing/query vectors,
ledger usage and denied requests before provider dispatch. Synthetic transport replaces every paid
request. Failure coverage retains uncertain usage while marking the document failed.
The full command uses the usual read-only app/tests/alembic mounts with
`docker compose -p asi-verification run --rm --no-deps -e RUN_POSTGRES_TESTS=1
-e EMBEDDING_PROVIDER=mock -e OPENAI_API_KEY= api uv run --frozen --extra dev pytest -q`.
Initial `lint.log` records extraction/import/line-length issues; `lint-final.log` passes Ruff.
`rebuild.log` records the isolated API rebuild with mock embeddings and an empty API key.
Startup logs verified migrations 0027/0028; `browser.log` passes ten Chromium tests in 28.9 seconds
against the rebuilt API, using `npx playwright test --project=chromium --reporter=line`.
All 17 tooling tests and documentation/source-size/whitespace checks pass; source coverage is 145
application files with 23 legacy exceptions. One existing Starlette/httpx deprecation warning remains.
This proves configured integration with synthetic responses and default-mode browser behavior;
real semantic quality, external billing, per-graph embedding limits and reconciliation remain open.

## Durable embedding admission
2026-09-07: `.artifacts/20260907-embedding-attempts/tests.log` records 48 passes and a real
foreign-key lock conflict: pending document inserts blocked independent workspace FOR UPDATE.
NO KEY UPDATE repaired that conflict; `after.log` records 20 affected PostgreSQL/budget/migration
tests passing in 55.73 seconds. Tests cover caller rollback isolation, concurrent admission,
unknown usage retention, cross-workspace finalization denial and actual provider dispatch ordering.
Revision 0028 refusal/rollback and safe downgrade/re-upgrade are verified with persisted rows.
The first full run (`full.log`) passed 354 tests and failed dataset pagination ordering.
`pagination-before.log` reproduces equal-timestamp instability. The query now has an ID tie-breaker,
and the original chronological test uses fixed timestamps without relaxing its expected order.
`full-final.log` passed 355 tests but failed evaluation pagination's equivalent clock assumption.
The four chronological pagination fixtures now share explicit timestamp setup, retaining their
original ordering assertions. `full-verified.log` passes all 356 tests in 198.79 seconds.
`lint-result.log` passes final lint; earlier lint logs retain the diagnosed formatting failures.
Commands use `docker compose -p asi-verification run --rm --no-deps -e RUN_POSTGRES_TESTS=1`,
read-only local app/tests/alembic mounts under `/app/`, and `api uv run --frozen --extra dev pytest -q`.
Lint uses those mounts with `api uv run --frozen --extra dev ruff check app tests
alembic/versions/0028_ai_attempt_status.py`. All providers are mocked; runtime embedding
configuration/integration and external billing reconciliation remain unverified.

## Embedding API boundary
2026-09-07: `.artifacts/20260907-embedding-api/tests.log` records 30 tests passing in 1.03 seconds;
`lint.log` records passing backend Ruff. The tests mock every HTTP/provider interaction, including
request shape, bounded reads, refusal to redirect, usage/index/model validation and sanitized
failure paths. Command: `docker compose -p asi-verification run --rm --no-deps`, read-only
app/tests mounts at `/app/app` and `/app/tests`, then `api uv run --frozen --extra dev pytest -q
tests/test_embedding_api.py tests/test_embedding_transport.py`. Lint uses the same mounts and
`api uv run --frozen --extra dev ruff check app tests`. One existing Starlette/httpx deprecation
warning remains. This verifies the API boundary, not runtime accounting or real semantic quality.
The request/response contract follows the
[OpenAI embeddings API](https://developers.openai.com/api/reference/python/resources/embeddings/methods/create).

## Embedding storage migration
2026-09-07: `.artifacts/20260907-embedding-storage/tests.log` records 33 passing affected tests
in 40.45 seconds, including `test_embedding_migration.py`, `test_budget_migration.py`,
`test_embedding_compatibility.py`, `test_knowledge_documents.py` and `test_retrieval.py`.
Command: `docker compose -p asi-verification run --rm --no-deps -e RUN_POSTGRES_TESTS=1`,
read-only app/tests/alembic mounts under `/app/`, followed by
`api uv run --frozen --extra dev pytest -q` and those five paths under `tests/`.
The new test creates and drops only `embedding_migration_<uuid>`, verifies existing vector values,
safe downgrade/re-upgrade and 1,536-dimensional ORM round-trip, then proves unsafe downgrade
leaves data and revision unchanged. Initial `lint.log` contains two formatting failures;
`lint-final.log` records the subsequent result. No existing application database was migrated.

## Embedding compatibility
2026-09-07: `.artifacts/20260907-vector-compatibility/before.log` records six reproduced failures.
`after.log` records 31 affected passing tests. After stored-vector regressions were added,
`full.log` records 318 passing backend tests in 154.51 seconds; `lint.log` records passing Ruff.
The full command used `docker compose -p asi-verification run --rm --no-deps`,
`-e RUN_POSTGRES_TESTS=1`, read-only mounts of local backend app/tests/alembic at `/app/`,
and `api uv run --frozen --extra dev pytest -q`. Lint used the same app/tests mounts with
`api uv run --frozen --extra dev ruff check app tests`. One existing Starlette/httpx deprecation
warning remains. Nine new tests prove model/provider exclusion, lexical independence,
explicit malformed-vector errors and compatible evidence. No paid provider calls were made.
This does not prove semantic retrieval quality or complete provider integration.

## What each layer proves

| Check | Scope | Does not prove |
| --- | --- | --- |
| Source-size tests/checker | New file limits and legacy growth | Architectural cohesion |
| Backend pytest | Domain/API behavior with SQLite and mocks | PostgreSQL concurrency or real AI quality |
| Ruff | Selected Python lint rules | Correct permissions or business behavior |
| Frontend typecheck/build | Types and production asset compilation | User journeys |
| Playwright | Real browser and running API interactions | Every role/language unless explicitly covered |
| Compose startup/migrations | Boot on PostgreSQL/pgvector | Restore, upgrade safety or production readiness |

## Local baseline commands

Windows automatic verification: `./scripts/verify.ps1` from the repository root. It builds
and runs the stack, checks tooling/source-size policy and HTTP readiness, runs the backend
suite/lint, frontend build/audit and browser tests, then
captures runtime logs. Results and duration for each command are retained in `checks.json`.
The commands below remain useful for a focused diagnosis without rerunning the whole loop.

Run from the repository root unless noted. Use Docker Desktop and a free local port set.
`asi-verification` has its own Compose volume; do not reuse another project's database.

```text
docker compose -p asi-verification up -d --build
docker compose -p asi-verification ps
docker compose -p asi-verification exec -T api alembic current
python -m unittest discover -s scripts/tests -v
python scripts/check_source_sizes.py
```

From `backend/`, use native `uv run pytest -q` after `uv sync --frozen --extra dev`.
If the native environment is incompatible, this PowerShell command runs tests in a disposable
container using the current image (rebuild after backend source changes):

```powershell
docker compose -p asi-verification run --rm --no-deps -v "${PWD}/backend/tests:/app/tests:ro" api uv run --frozen --extra dev pytest -q
```

From `frontend/`:

```text
npm ci
npm run build
npx playwright install chromium
npm run test:e2e
```

## Evidence contract

Save each run under `.artifacts/<timestamp>/`: command output, exit code, duration, revision,
container state, dependency audit and browser JSON results/traces/screenshots. Record the
dirty working-tree state too; HEAD alone does not identify an uncommitted application build.
Do not overwrite failing evidence with a successful retry. Use synthetic accounts/content.
Logs and traces may include sensitive data; keep artifacts ignored and review before sharing.

Playwright supports `--reporter=line,json --trace=on --output=<artifact-directory>` and
`PLAYWRIGHT_JSON_OUTPUT_NAME` for results. Capture API logs with
`docker compose -p asi-verification logs --no-color --timestamps api`.

## Verified baseline: 2026-09-07

- Clean PostgreSQL upgrade through revision 0025; API health and frontend HTTP 200.
- Backend: 192 passed, one Starlette/httpx deprecation warning, 81.08 seconds.
- Frontend production build: passed.
- Browser: 1 passed, 2 failed; evidence in `.artifacts/20260907-baseline/`.
- Initial npm audit: two vulnerable transitive dependencies, subsequently updated.

## Latest verification: 2026-09-07

- Full runner evidence: `.artifacts/20260907T085932737Z/`; 10 of 11 commands passed.
- Backend: 197 passed, one Starlette/httpx deprecation warning; Ruff passed.
- Frontend: clean install and production build passed; npm audit reported zero vulnerabilities.
- Browser in that run: 2 passed, 1 failed because polling missed the short toast fade phase.
- The toast test now uses Playwright's clock to advance through visible, dismissing and hidden
  states without relying on wall-clock polling. Product timing is unchanged.
- Repeated suite: `npx playwright test --project=chromium --repeat-each=3 --reporter=line,json
  --trace=on`; 7 passed, 2 failed in `.artifacts/20260907-clock-fix/`. All three toast executions
  passed. Two agent-editor executions exposed saved values overwriting ongoing typing.
- Source-size policy: 9 tests passed; 125 application files checked with 24 legacy exceptions.
- Live `/health` response request ID matched a structured HTTP log record. This does not prove
  workflow correlation or privacy of other loggers.

The subsequent agent-draft repair passed all 9 repeated executions in
`.artifacts/20260907-agent-draft-final/` (66.1 seconds). The test deliberately holds a list
response until after an edit, then checks draft preservation, failed-save retention and retry.
It fails against the original shell at the empty-draft assertion; evidence is retained in
`.artifacts/20260907-agent-draft-red/`. Final build and source-size checks also passed
(126 application files). No backend code changed in this repair.

Retain intermediate failures: an earlier run (`20260907-agent-draft-v2`) had one evaluation
setup request fail with a socket hang-up, alongside 8 passes. Captured API logs showed no
matching exception; the later passing run does not establish its cause or eliminate the risk.
See the [agent editor repair ticket](tickets/agent-editor-response-race.md).

## Required next coverage

RAG baseline replacement: `.artifacts/20260907-rag-baseline/`. The old image failed all three
multilingual seven-day policy cases. The corrected implementation passed 50 affected tests,
then seven final focused regressions and all three live browser journeys (26 seconds). Lint,
documentation and source-size checks passed. Mock generation quotes bounded evidence; these tests
prove the execution/accounting contract, not semantic embedding quality or factual entailment.

Direct evaluation provider repair: `.artifacts/20260907-evaluation-provider/`. The two configured
transport regressions failed before the routing change; 25 evaluation/model-config tests passed
afterward. Final focused cases also prove cross-workspace denial prevents provider invocation.
Lint and the live browser evaluation/review journey passed. Transport was stubbed; no real-provider
quality or paid execution claim follows from these tests.

Current-version retrieval repair: `.artifacts/20260907-retrieval-versions/`. Three multilingual
regressions failed on obsolete version-1 results before the fix. Afterward, 25 retrieval/knowledge
tests and 24 agent tests passed; lint passed. Live PostgreSQL upload/reindex/search probes returned
only version 2 with citations in EN/JA/ZH. Historical versions remain stored. This verifies current
evidence selection, not embedding quality or the entire browser journey.

Signing-configuration repair evidence: `.artifacts/20260907-production-config/`. Full backend
run passed 214 tests before five more edge cases were added; the final focused configuration
suite passed 22 cases and backend lint passed. Application import rejected the default production
key and accepted an ephemeral random key without exposing it. This is not a production deployment.

Latest full runner: `.artifacts/20260907T101634809Z/`, all 14 checks passed, including 13 tooling
tests, 197 backend tests, 3 browser journeys, frontend build/audit, startup/readiness and logs.
The readiness CLI also returned exit 1 against an unavailable endpoint. This run completed
before the documentation consolidation; no application edits were made during that docs pass.
The documentation pass added `python scripts/check_docs.py` and three failure/boundary tests:
the documentation gate and all 16 tooling tests pass. The runner now has 15 checks; the earlier
14-check full-run record is retained with its actual scope.

The CI browser job now defines fresh-stack migration startup and browser journeys on PostgreSQL,
with always-run log capture and seven-day artifact retention. It has not yet run on GitHub;
local validation cannot prove hosted-runner behavior or branch protection. Its endpoints
returning HTTP 200 is a startup check, not a production dependency-readiness contract.

Dedicated PostgreSQL upgrade/concurrency CI, the complete multilingual README journey, two-workspace
role-denial tests through the browser, provider failure and budget rejection, restart recovery,
backup restoration, and an explicit operational load target remain open.

Pending metric-contract evidence: `.artifacts/20260907-metric-contract/`. Three new regressions
fail against the old image; the affected evaluation suites pass 25 tests. Frontend build and
all three Chromium journeys pass (25.5 seconds). Backend `ruff check app tests` fails one E501
at `app/services/evaluation_metrics.py:31`; this run is not an overall pass. Application edits
are preserved during the documentation-only review. The subsequent implementation pass fixed
that formatting error; `lint-final.log` records passing backend lint. See the
[completed plan](exec-plans/completed/evaluation-metric-contract.md).

After the lint fix, the full backend suite passed **234 tests** in 92.16 seconds. Evidence:
`.artifacts/20260907-metric-contract/backend-final.log`. Command: `docker compose -p asi-verification
run --rm --no-deps` with current `backend/app` and `backend/tests` mounted read-only, followed by
`api uv run --frozen --extra dev pytest -q`. One Starlette/httpx deprecation warning remains.
This is a complete backend test run, not a full rerun of the 15-check verification script.

## PostgreSQL review transaction checks

The local verifier now enables `RUN_POSTGRES_TESTS=1`; CI's backend job provisions PostgreSQL,
applies migrations and enables the same tests. Hosted execution remains unverified. To run only
this boundary after building the API, use:

```powershell
docker compose -p asi-verification run --rm --no-deps -e RUN_POSTGRES_TESTS=1 api uv run --frozen --extra dev pytest -q tests/test_review_transactions.py
```

Tests use a random `review_test_<uuid>` schema, independent sessions and bounded synchronization.
The schema is removed afterward; existing application tables are preserved. PostgreSQL's vector
extension must already exist (the migration creates it). Without the opt-in variable these tests
skip; a SQLite-only run is not concurrency evidence.

Evidence: `.artifacts/20260907-review-transactions/`. The first setup failed because pgvector's
type was outside the isolated search path; `before.log` retains that failure. Corrected setup
then exposed all four regressions on the old image (`before-race.log`). Initial repaired
PostgreSQL plus review API checks passed 13 tests (`after.log`); a fifth stale-session regression
was subsequently added. Three browser journeys pass in 24.6 seconds (`browser.log`).
Final full backend run passed **239 tests**, including all five PostgreSQL cases, in 99.51 seconds
(`backend-final.log`); one Starlette/httpx deprecation warning remains. Final lint passes
(`lint-final.log`). Independent code review found no P0/P1 in this boundary. This does not prove
atomic publication of the initial review queue record or run-level budget admission.

Subsequent graph publication repair evidence: `.artifacts/20260907-review-publication/`.
Six injected guardrail/review storage failures fail on old code; three normal publication cases
pass. The repaired affected suite passes 48 tests, including PostgreSQL visibility checks;
three browser journeys pass in 19.4 seconds. The tests isolate final persistence with mock graph
output; EN/JA/ZH cases prove language metadata preservation, not real-model multilingual quality.
An independent code review found no scoped P0/P1. Process termination, persistent outages and
lost commit acknowledgments are not covered by these tests and remain reliability work.
Final focused publication run passes 11 tests (`final.log`), and final backend lint passes
(`lint-final.log`). The earlier import-lint failure is preserved in `lint.log`.

Budget reservation storage/service evidence: `.artifacts/20260907-budget-reservations/`.
Nine PostgreSQL accounting/concurrency tests pass. A combined run adds the migration test and
passes 10 tests: fresh disposable database upgrade, downgrade to 0025, and re-upgrade to 0026.
The migration test requires a PostgreSQL test user with CREATE DATABASE permission; it drops
only its generated `budget_migration_<uuid>` database. Lint passes. These tests verify the new
service, not model invocation. At that checkpoint provider/graph integration remained open;
the subsequent runtime verification below closes that scoped gap in the
[budget plan](exec-plans/completed/run-budget-enforcement.md).
The subsequent finalization-lock regression passes separately (`finalization-lock.log`), proving
reconciliation waits while an admission transaction owns the workspace snapshot.

## Graph budget runtime verification
Evidence: `.artifacts/20260907-budget-runtime/`. `before.log` and `after.log` contain an invalid
test URL (/run instead of /runs); those failures are fixture errors, not runtime evidence.
With the route corrected, `before-corrected.log` records six failures when the graph is explicitly
wired to its prior unreserved ConfiguredModelProvider. `after-corrected.log` passes 19 tests with
the reserved boundary. No application code was reverted for that controlled comparison.

Independent review found uncertain successful usage was releasing allowance too early. After
repair, `final-focused.log` passes 25 tests, covering missing/partial/invalid usage, actual HTTP
request output caps, uncertain timeout retention, and PostgreSQL wrapper dispatch concurrency.
`isolation-context.log` passes 12 accounting/isolation/model-context tests. `browser.log` passes
three Chromium journeys in 22.1 seconds; `migration.log` reports 0026 head. Backend lint passes
in `lint-verified.log`; prior lint failures remain retained.

The initial complete backend run passed 270 tests in 132.36 seconds (`full-backend.log`), before
the added review regressions. Tests use deterministic providers or stubbed transport, never paid
calls. The provider cap and byte allowance do not prove exact external billing or late usage
after reservation expiry. See [token economy](token-economy-design.md) for those boundaries.
The final complete run passes **277 tests** in 136.49 seconds (`full-final.log`), with one
Starlette/httpx deprecation warning. This includes the added review regressions, PostgreSQL
dispatch/isolation checks and disposable-database migration verification.

## Multilingual workflow failure
Evidence reviewed 2026-09-07: `.artifacts/20260907-multilingual-workflow/before.log` records
three failing EN/JA/ZH cases in `frontend/tests/e2e/multilingual-workflow.spec.ts`. Each imports
a seven-day policy, runs the agent and fails at the answer-content assertion: the mock graph
returns 30 days instead. Current `support_agent_graph.py::_mock_answer` contains those canned
policy strings. Repair is pending; earlier green backend/browser runs do not cover this case.

Reproduce against the isolated running stack from `frontend/`:
```powershell
npx.cmd playwright test tests/e2e/multilingual-workflow.spec.ts --project=chromium --reporter=line
```
These tests use Playwright's HTTP request API, not browser page interactions. They stop before
their trace, review, evaluation, cost and isolation assertions; those later checks remain
unverified by this run. The fixture includes the question in the document for deterministic
mock retrieval; it does not prove semantic retrieval quality. An earlier output-directory
error prevented test execution and is not behavioral evidence. This documentation audit
reviewed the retained failure without changing application code or rerunning the live journey.


## Multilingual policy repair verification
The failure above is repaired by `mock_support_answer.py`: the graph mock quotes at most 800
source characters, marks truncation, includes the exact citation and labels itself as simulation
in EN/JA/ZH. It makes no policy applicability decision. The Chinese regression now preserves
its source's account-status condition instead of asserting the old canned paraphrase.

Evidence in `.artifacts/20260907-multilingual-workflow/`:
- `backend-focused.log`: 37 tests pass, including seven new excerpt regressions.
- `backend-full.log`: 284 tests pass in 134.18 seconds, one Starlette/httpx deprecation warning.
- `after.log`: policy assertions pass, but all cases stop at a fixture error reading upload
  `id` instead of `document.id`. This is not an application failure; the schema confirms the envelope.
- `corrected.log`: all three EN/JA/ZH HTTP journeys pass in 4.7 seconds after fixture correction.
- `browser.log`: three browser regressions plus three HTTP journeys pass in 20.2 seconds.
- `lint-final.log` and `frontend-build.log`: backend lint and frontend build pass. The initial
  import-order lint error remains in `lint.log`.

The HTTP journeys exercise register/login, workspace, dataset/document upload, agent answer and
exact citation, trace/ledger, unsafe-case review rejection, three evaluation modes, cost summary,
and resource isolation under another workspace owned by the same user. They do not prove
outsider/role denial or a complete multilingual browser journey. Providers are mocks; semantic
retrieval and factual entailment remain release gaps. No paid provider calls were made.


## Multilingual browser acceptance
Evidence: `.artifacts/20260907-browser-acceptance/`. The new
`frontend/tests/e2e/multilingual-browser.spec.ts` uses visible controls for registration/login,
workspace creation, dataset import, document upload, agent creation/run, trace navigation,
unsafe-run rejection, evaluation and cost inspection in EN/JA/ZH. It observes responses to
verify persistence without API setup mutations or injected auth tokens. Browser exceptions
fail the journey. Each successful language run saves a costs screenshot.

The initial runs reproduced a blank page after dataset import. `diagnostic.log` identifies
React's hook-count exception: pages called stateful FolderPicker directly as a render callback.
Three shell adapters now return a JSX component, preserving hook ownership as list sizes change.
The later `fourth.log` failure and snapshot show background run refreshes navigating away from
Human review to Traces. Removing the delayed automatic navigation preserves the user's chosen
page; the explicit Inspect trace action remains. The shell shrank by one line to 8,067.

`repaired.log` and `third.log` also retain selector failures; language/decision selects now use
scoped combobox roles. `third.log` contains one Failed to fetch exception without an established
cause; it did not recur in the final run and remains preserved for diagnosis if repeated.
`fifth.log` passes the complete English UI journey in 8.6 seconds. `final.log` passes all nine
Playwright tests in 26.4 seconds: three complete language UI journeys, three HTTP journeys and
three existing browser regressions. `build-final.log` passes TypeScript and production build;
documentation, source-size and whitespace checks pass. Backend code did not change in this
repair, so the prior 284-test backend result remains dated evidence, not a new run.

These are mock-provider, single-owner happy-path and unsafe-rejection journeys. They do not
prove semantic relevance, real-provider factual support, complete role denial, multi-user
concurrency or production recovery. UI verification is stronger than the prior HTTP-only
journey but does not close those release requirements.


## Workflow authorization boundary verification
`backend/tests/test_workflow_authorization.py` seeds actual dataset, document, agent, run,
review and evaluation resources using owner operations. It checks 12 read paths for both
anonymous (401) and outsider (404) access, with successful owner reads as positive controls.
Responses must not reveal protected sentinel names, document IDs or run IDs.

The mutation matrix checks anonymous/outsider/viewer/reviewer denial for imports, uploads,
agent creation/execution, evaluation and resource deletion, plus unauthorized retrieval and
review resolution where applicable. Spies fail if denied requests enter RetrievalService.search,
SupportAgentGraphRunner.run or EvaluationRunner.run_from_jsonl. Graph-run, graph-step, AI-run,
retrieval-trace and evaluation counts remain unchanged. Owner document/dataset reads still
succeed afterward. A separate case verifies reviewer denial for dataset/evaluation/audit reads,
developer denial for review resolution, and successful reviewer rejection of the same run.

Evidence: `.artifacts/20260907-workflow-authorization/final.log` passes 13 tests in 14.08 seconds
(seven matrix cases plus six existing retrieval tests), with one Starlette/httpx warning.
`lint-verified.log` passes. `first.log` retains two fixture failures: the positive owner check
caught a nonexistent GET agent-detail route; it was corrected to the actual summary route.
Two line-length lint failures are preserved. No application code changed, so this is new
boundary evidence rather than a security repair or a fresh full backend/browser run.

These tests use SQLite with actual FastAPI authentication/permission dependencies and deterministic
providers. They do not cover every route, folder mutation, archived-workspace transition,
malicious JWT variation, browser role journey or PostgreSQL concurrency boundary. Those need
separate evidence; do not extrapolate this matrix into a complete authorization certification.


## Answer citation validation
Evidence: `.artifacts/20260907-answer-citations/`. `before.log` reproduces six failures on the
old image: retrieval metadata let uncited, empty or invented-reference drafts pass citation
checks, and uncited EN/JA/ZH provider responses finalized. The shared `answer_citations.py`
check now requires an exact citation from nonempty packed context in the draft. Routing rules
were extracted to `graph_routing.py`; publication uses the same check. Graph size fell from
761 to 732 lines and the exception baseline was lowered.

`after.log` passes 52 affected tests, including ten new cases for exact references, trimmed/empty
sources, empty drafts and three-language provider responses. Uncited drafts have two ledger
records, a review proposal, failed citation guardrail, no final answer and no finalize node.
`full.log` passes 301 backend tests in 147.87 seconds with one Starlette/httpx warning.
`browser.log` passes all nine browser/API journeys in 26.0 seconds against the rebuilt API.
`lint-final.log` passes; the initial line-length failure remains in `lint.log`. Documentation,
source-size (138 application files) and whitespace checks pass. No paid calls were made.

Default policy routes citation failures to review. Existing disabled/record-only overrides
remain effective. Exact citation presence does not establish claim support or reject every
additional fabricated reference when a valid reference is also present. Semantic relevance,
claim-level entailment and refusal detection remain separate release requirements. The final
catalog description was clarified to match this boundary; it introduces no behavioral change.


## Mock retrieval relevance and refresh recovery
Evidence: `.artifacts/20260907-mock-retrieval/`. Four regressions fail in `before.log`: matching
synthetic vectors gave unrelated EN/JA/ZH content 0.35 relevance, and default search unnecessarily
called the hash embedding provider. Default mock retrieval now uses lexical ranking, reports
`lexical` in traces, emits null vector scores and skips query embedding generation. Explicit
vector evaluation remains synthetic; injected non-mock providers can still use hybrid scoring.

`after.log` passes 44 affected tests. The initial full run (`full.log`) passed 304 and failed
one budget test because a singular refund query missed plural Refunds. Conservative English
plural normalization repaired the real search regression; budget assertions were unchanged.
`full-final.log` passes 309 backend tests in 153.77 seconds, one Starlette/httpx warning.
`lint-final.log` passes. This is lexical matching, not stemming completeness or semantic search.

The first live nine-test run passed, but `browser-final.log` later reproduced the intermittent
Failed to fetch exception in loadBudgetPolicy during refreshWorkspaceData. The workspace effect
launched refresh without a rejection handler. A forced network abort reproduces missing error
feedback in `refresh-before.log`; the effect now reports an explicit UI error. The new browser
case verifies the error, no unhandled exception and successful recovery using Refresh.
`browser-verified.log` passes all ten tests. `frontend-build.log` passes TypeScript/build.
Documentation, source-size and whitespace checks pass. The original failing logs are retained.

No paid providers were used. Lexical overlap can miss synonyms or match generic wording; it does
not establish answer support. Threshold zero can intentionally return zero-overlap candidates.
The refresh repair covers the workspace refresh effect, not all asynchronous loaders or stale
workspace-response handling. Full semantic retrieval and general network-failure handling remain open.

### 2026-09-08 default UI rollout

With FRONTEND_URL=http://localhost:5174, all five rebuild journeys passed in 39.1s
against /. After the keyboard skip-link correction, rebuild-core.spec.ts and
session-recovery.spec.ts passed 9/9 in 38.2s. Legacy session tests explicitly use
/legacy.html; existing behavior assertions remain intact. npm run build passed.
Docker frontend alone was rebuilt; Chrome verified the default entry at localhost:5173.
These checks use mock providers and do not establish production readiness.

### 2026-09-08 remake database restore acceptance

`python scripts/verify_database_restore.py` passed in 34.546s at revision
0036_task_attempts. Evidence: `.artifacts/database-restore-34ffe983d12d47f38dc06f10fa1ceb45/report.json`
and application.log; archive size 6,370,979 bytes. All 41 public tables matched counts and
ordered content fingerprints; source manifests stayed unchanged. Updated application probes
passed EN/JA/ZH restored login, retained reads, isolation denial, durable task admission,
idempotent admission replay, worker execution, cited output and history reads. Each language
also passed queued stop followed by worker execution with no model calls or action proposals.
The temporary database was dropped; an independent pg_database lookup confirmed absence.
Two restore harness tests passed (including injected failure/cleanup cases); scoped Ruff and
diff checks passed. These are mock-provider local logical recovery checks, not active-call
cancellation, browser cutover, offsite disaster recovery or real-provider quality evidence.

### 2026-09-08 active cancellation in Chrome

Run fc0559c6-af82-43d6-9850-b1f83451f651 was submitted through Chrome in the QA
EN/JA/ZH workspace. With no active runs, the ordinary worker was paused and a one-run
worker wrapper delayed MockModelProvider.complete until a stop request, then held the
response for 15 seconds. Chrome showed Running, Stopping with its pending explanation,
and Stopped after the response returned. Reload preserved Stopped, partial model accounting
and no final answer. SQL confirmed zero proposals, zero task notes and only detect_language
and classify_intent steps. No browser console errors. The ordinary worker was restarted.
The ignored harness is `.artifacts/active-stop-probe.py`; no application delay was added.
This verifies cancellation while a mock provider call is pending, not real network cancellation
or reversal of charges. The model ledger measures the mock computation; graph step time
also includes the injected wait.

QA exposed a stale list: detail showed Running/Stopping while the row still showed Queued.
useRunTrace now refreshes the parent on each status change. rebuild-status.spec.ts verifies
Queued/Running/Stopping/Stopped agreement without manual refresh and after reload using
controlled API responses. That test plus the real core journey passed 2/2 in 23.1s;
TypeScript/Vite build passed. The frontend container was rebuilt with the fix.

### 2026-09-08 Chrome ingestion failure recovery

A one-use service probe injected an unavailable embedding provider when creating synthetic
QA document 4223378d-995c-4f75-b7f4-39a5455f1362. This used KnowledgeService's real failure
path, not a manually changed status. Chrome displayed Failed, the reason, preserved text
and Edit and retry. Saving the unchanged text through Chrome returned Ready at version 2
and removed the error. SQL independently confirmed indexed, no error, two versions and
one chunk. Browser console errors: none. Harness: `.artifacts/ingestion-recovery-probe.py`.
Failure creation was service-driven; recovery was browser-driven with the normal mock
embedding configuration. This does not verify a real external provider outage.

### 2026-09-08 execution context visibility

Run context now shows the initiating user ID, agent ID, trace ID and timestamps from the
existing run API. Core browser checks compare IDs with the actual admission response.
Core/status journeys passed 2/2 in 21.3s; TypeScript/Vite passed. The frontend image was
rebuilt. Read-only provider readiness inspection returned no configured API key and mock
embeddings; real-provider verification remains unavailable. No secrets were printed.

### 2026-09-08 responsive layout acceptance

rebuild-responsive.spec.ts uses a fresh workspace with long unbroken workspace/agent names
and checks all five areas at 320px and 768px, including knowledge and agent editors. Initial
Work overflow was 156px; screenshot/trace are preserved in `.artifacts/responsive-initial-failure`.
Fixed grid minimum sizing, form-control constraints and action wrapping. Screenshot review
also found squeezed tablet header buttons and hidden phone navigation; header buttons now
retain width and phone navigation wraps. Final responsive test passed in 4.8s; core plus
responsive passed 2/2 in 20.1s before the final CSS-only polish. TypeScript/Vite passed before
that polish. Screenshots are emitted to frontend/test-results for all ten area/width pairs.
Reviewed Work/Agents phone and Settings tablet renders. These cover the listed states,
not a complete accessibility audit or every populated/expanded combination.

### 2026-09-08 agent search

Added the missing Agents search control using the existing bounded workspace API, with
page reset and a no-match state. Search length is bounded to the API's 120 characters.
The responsive journey verifies no-match and matching results, then opens the found agent
at 320px and 768px. Core plus responsive/search passed 2/2 in 19.9s; build passed.
No backend authorization or query behavior changed.

### 2026-09-08 trace response redaction

`pytest tests/test_trace_redaction.py tests/test_agents.py -q` passed 27 tests in 42.28s.
Tests cover nested serialized payloads, known credentials/email masking, multilingual and
citation preservation, unchanged stored evidence, and anonymous/foreign-workspace denial.
Scoped Ruff passed. After rebuilding the API, core and action browser journeys passed 2/2
in 27.6s, including citations, review decisions, retries and stopping. Documentation and
diff checks passed. See observability-design.md for the exact redaction boundary and limits.

### 2026-09-08 saved agent configuration

Task configuration and task API tests passed 4/4 in 6.33s, including snapshot preservation
after agent edits, response whitelist/redaction and anonymous/foreign denial. CLI tests
passed 14/14 in 2.97s. Scoped Ruff and frontend build passed. After API/frontend deployment,
core browser passed in 18.9s with saved configuration expanded. Installed asi run inspect
returned the same configuration from a historical task; evidence is
`.artifacts/cli-snapshot-evidence.json`. No paid model call or schema migration was needed.

### 2026-09-08 role transition audit

Current hierarchy/auth/workspace regression passed 31 tests in 22.43s. PostgreSQL hierarchy
migration/concurrent-owner-leave/stale-admin authority test passed in 4.41s. These verify
the existing mixed-role implementation, not completion of legacy retirement. The user has
now authorized removing unnecessary legacy system paths; retirement requires updated
four-role contract/migration evidence and preservation of relevant isolation/recovery tests.

### 2026-09-08 four-role assignment contract

Hierarchy, auth/workspace, evaluation and guardrail tests passed 51/51 in 85.17s after
restricting public role assignment to Viewer/Operator/Admin/Owner. Retired-role requests
are now invalid input (422), including Owner requests; valid-role authority failures retain
their existing denial checks. Fixtures that created legacy members now create Operators.
Historic-role permission fixtures inserted directly remain unchanged pending migration.
Scoped Ruff and frontend build passed. Legacy browser tests requesting Reviewer are pending
porting and are not covered by this pass.

After API/frontend deployment, rebuild-members.spec.ts passed in 5.6s against the new contract.

### 2026-09-08 restricted-role browser migration

Ported restricted-role-security.spec.ts and its fixture from legacy UI/Reviewer/synchronous
runs to the new interface, Viewer/Operator and durable tasks. Both live browser journeys
passed in 10.7s. Preserved scoped retrieval, foreign-document filtering, foreign workspace
404s, denied writes, unchanged accounting after denials, retained document list and session
checks. Viewer task admission/stop/review is denied; Operator admission/stop/rejection succeeds.
Removed the obsolete Reviewer-dashboard test from review-ux-smoke.spec.ts after this pass;
retired Reviewer UI capabilities are no longer the product contract. The earlier legacy
folder/review editing test remains pending retirement or migration.
