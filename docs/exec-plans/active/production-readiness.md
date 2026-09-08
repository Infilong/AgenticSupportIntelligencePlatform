# Production readiness improvement

## Goal
Make every README promise demonstrably work for a small-team production deployment. Continue
automatically through inspected, implemented, tested and reviewed increments until that full
objective is verified. A passing narrow check does not redefine completion.

The user refined the objective on 2026-09-07: prioritize the real EN/JA/ZH workflow from
register/login, workspace, dataset and knowledge ingestion through grounded agent response,
trace inspection, human review, evaluation and cost results. Priorities are P0 application/
security/isolation, P1 broken critical flows/AI behavior/verification, then reliability and
observability, maintainability and finally optional enhancements. No known P0/P1 may remain.

## Context
2026-09-08 recovery UI implemented: frontend build and four focused browser checks pass on the
rebuilt Compose frontend. Reasons survive failures; refresh handles a lost response without replay;
recovery and billing remain separate. Full browser runs currently pass 28/29: editor initial
navigation spends roughly 56 seconds in Chromium DNS timing. No assertion/timeout was weakened.
Next investigate [browser navigation delay](browser-navigation-delay.md); no test process is
still running. Full acceptance remains unproven despite focused recovery success.

2026-09-08 embedding orphan recovery API passes 103 embedding/ownership tests with PostgreSQL
and Ruff (`.artifacts/embedding-recovery-broader.log`, 120.89s). A test-created mock-dispatch
process is terminated and recovered through the real API without releasing estimated usage;
concurrent recovery, permission boundaries and audit rollback pass. Rebuilt isolated API healthy.
All processes completed. Next: Costs UI recovery controls and browser verification, then
model-call recovery in the [active plan](interrupted-call-recovery.md).

2026-09-08 embedding ownership integration passes 92 PostgreSQL-enabled embedding/ownership/
migration tests and Ruff in `.artifacts/embedding-ownership-broader.log` (135.39s). New
embedding attempts carry ownership provenance and finish on the owned connection; stale
database owners cannot publish vectors. The rebuilt isolated API is healthy on migration0032.
All processes completed. Next: audited orphan recovery and process-crash/race tests in the
[active recovery plan](interrupted-call-recovery.md); model calls still lack this protocol.

2026-09-08 recovery foundation: the
[ownership design](../../design-docs/interrupted-execution-ownership.md) and PostgreSQL helper
pass four database-backed tests and Ruff (`.artifacts/execution-ownership-verified.log`).
This is not runtime integration. Next add durable protocol metadata and owned-connection
embedding finalization before exposing pending-attempt recovery. All test processes completed;
the [recovery plan](interrupted-call-recovery.md) remains active.

2026-09-08 unresolved reservation safety: expired reserved allowance now remains in admission
and blocks evaluation deletion until explicit finalization. Two regressions reproduced budget
reuse/deletion; Ruff and 119 budget/provider/embedding tests pass with PostgreSQL enabled in
`.artifacts/reservation-expiry-verified.log`. All processes completed. Next implement the
ownership/fencing design in [interrupted-call recovery](interrupted-call-recovery.md); this
repair retains unknown usage but cannot yet recover orphaned pending calls.

2026-09-08 loaded-case identity: new score fingerprints and contract v2 now reject comparisons
with changed inputs, expectations or duplicate counts while allowing reordered identical cases.
Ruff and all 103 evaluation tests pass in `.artifacts/evaluation-identity-final.log` (75.66s).
All processes completed. This postdates the full pipeline below; no dedicated browser rerun.
Next: model/embedding interrupted-attempt recovery remains open. Case identity does not prove
equivalent knowledge indexes, prompts or model configuration; preserve those limits when
interpreting deltas. See [case evidence](../../testing.md#evaluation-loaded-case-identity).

2026-09-08 cumulative verification: the full pipeline passes all 17 gates in
`.artifacts/20260908T004216702Z/`: 669 backend tests, 27 development-stack browser tests and
27 compiled-image browser tests. Runtime review finds no server/error outcomes in either
captured window. All processes completed; see [full evidence](../../testing.md#full-regression-after-evaluation-contract-repairs).
Next identified gaps were evaluation input provenance and recovery of interrupted model/embedding
attempts. Read-only inspection confirms pending embedding attempts cannot be reconciled by the
existing uncertain-attempt endpoint. A safe recovery design must distinguish live ownership
from orphaned work; elapsed time alone must not authorize replay or release billable usage.

2026-09-08: [comparison provenance](../completed/evaluation-comparison-provenance.md) now
stamps new results and suppresses deltas for missing/mixed/incompatible scoring contracts.
All 98 evaluation tests and Ruff pass in `.artifacts/comparison-provenance-acceptance.log`.
The cumulative runtime/browser verification is recorded above. Equivalent dataset/prompt/model
comparison inputs and critical quality/recovery gaps remain. Contract equality alone is not
experimental equality.

Latest verified increment (2026-09-08): [evaluation expectation coverage](../completed/evaluation-expectation-coverage.md)
removes untested cases from optional tool/guardrail quality denominators and preserves legacy
metrics under their original names. Scoring is extracted; 49 focused tests pass. Full local
verification passed all 17 gates in `.artifacts/20260908T000709309Z/`: 639 backend tests and
27 browser tests in each deployment mode. All verification processes completed. See
[full evidence](../../testing.md#evaluation-expectation-coverage-and-full-regression).

2026-09-08 follow-up: reproduced system prompt-token overcounts in all three languages (715 vs
611, 840 vs 738, 836 vs 734). System evaluations now sum scoped AI ledger prompt tokens and
model cost instead of step summaries. Ruff and 24 focused tests pass; all 72 evaluation tests
pass in `.artifacts/evaluation-usage-broader.log` (61.72s, PostgreSQL enabled).
Historical results remain unchanged; the UI does not distinguish their accounting versions.
2026-09-08 case-limit follow-up: 16 regressions reproduced ignored/invalid max_prompt_tokens.
The loader now validates nullable nonnegative database-range integers; scoring checks measured
prompt usage in every mode. The limit is post-execution acceptance, distinct from admission.
Ruff and all 88 evaluation tests pass in `.artifacts/case-token-limit-verified.log` (65.24s).
All 19 case-limit tests, including three additional rejected-import atomicity cases, pass in
`.artifacts/case-token-limit-boundary.log` (4.68s). Historical scores are not retroactively corrected.

Previous verified increment (2026-09-08): [cited duration support](../completed/answer-duration-support.md)
now routes invented numeric deadlines to review despite valid citations, without extra model
calls. The full pipeline in `.artifacts/20260907T234548644Z/` passes 17/17 gates: 632 backend
tests and 27 browser tests in each deployment mode. All processes completed. See
[full evidence](../../testing.md#cited-duration-support-and-full-regression).
Broader factual support remains unverified; this check compares quantities, not meaning.
Continue to remaining permission, AI-quality and recovery gaps.

Prior verification (2026-09-08): graph sequencing acceptance is complete. The full local
pipeline passed all 17 gates in `.artifacts/20260907T232714310Z/`: 609 backend tests,
27 development-stack browser tests, 27 compiled-image browser tests, lint/build/types,
repository gates, migration 0031 and HTTP privacy. All processes have completed; no test is
waiting. See [full evidence and limits](../../testing.md#full-regression-after-graph-sequencing).

The earlier intermittent editor-summary stall remains unexplained. Chromium transport
metadata is now attached; a synthetic route-lifecycle probe passed 80/80 without confirming
the suspected race. Preserve failing traces and use the diagnostics on recurrence rather than
claiming the stall fixed. Continue to remaining permission, AI quality and recovery gaps;
passing local tests do not establish hosted CI or release readiness. Recent embedding work is
tracked in the [semantic retrieval plan](semantic-retrieval.md); completed increments are in
the [execution index](../README.md).

The user authorized automatic implementation, startup, tests and evidence capture on 2026-09-07.
Use only OpenAI tools/skills. Commits, merges, publication and paid provider calls require their
own authorization. Preserve unrelated work and use the isolated `asi-verification` Compose stack.
The [audit](../../audits/production-readiness-2026-09-07.md) records original findings;
[quality score](../../QUALITY_SCORE.md) is the current status map.

## Requirements
Implement the product's EN/JA/ZH journey with workspace isolation, safe AI behavior, attributable
cost/traces, explicit human review and demonstrated operational recovery. Follow
[architecture](../../../ARCHITECTURE.md), [reliability](../../RELIABILITY.md) and relevant designs.

## Non-goals
Unrequested enterprise SSO, Kubernetes, multi-region scale, production publication or paid calls.
Do not replace functioning boundaries with broad rewrites or invent implementations for a demo.

## Acceptance Criteria
- Full README journey works through a browser with EN/JA/ZH examples and isolated workspaces.
- Authentication, role denial, cross-workspace retrieval and management boundaries are tested.
- Provider behavior has controlled verification, valid eval baselines, supported citations,
  output limits, spending admission and attributable usage/failure records.
- Concurrent review decisions and budget reservations cannot overwrite or overspend.
- PostgreSQL migrations/integration pass; browser gates run successfully in hosted CI.
- Runtime logs correlate request/workflow failures without secrets or PII.
- Production startup rejects unsafe configuration; restore, restart and rollback behavior are
  demonstrated against explicit workload and recovery targets.
- Documentation reflects capabilities and limits; architecture boundaries are enforced and
  oversized responsibilities are recovered in tested increments.

## Plan
Continuation prompt for the next Codex session:
1. Read the latest user request first, then inspect current worktree, live process handles,
   this plan and the relevant quality row/ticket. Apply the remaining steps only within that scope.
2. Reproduce the highest-impact gap. Keep local test data isolated; never restart from a stale
   process observation. Read the owning guide and identify a small responsibility split.
3. Implement the authorized increment; add meaningful failure/permission regressions and keep
   source limits. Never weaken tests, errors or accounting to achieve green results.
4. Run affected checks, broaden when the boundary warrants it, and capture commands, exit codes,
   durations and runtime/browser artifacts under a fresh `.artifacts/` directory.
5. Review and fix; update the owning docs, this plan and quality score as evidence changes.
6. Turn recurring failures into harness improvements. Continue to the next scoped gap; escalate
   only for a decision, missing credentials, unavailable permission or irreversible action.

Next sequence: complete denied-role/resource-management acceptance and remaining evaluation/P0/P1
gaps. Mock policy evidence now passes the live HTTP journey. Scoped atomic budget/review
repairs and the signing-key startup guard are complete; other
deployment configuration risks remain. Complete selection-change race coverage where it affects
the workflow. Verify hosted CI
when publication is authorized. Keep the remaining audit requirements intact.

## Verification
Use [testing](../../testing.md) and [scripts](../../../scripts/README.md). Backend tests use mocks
with SQLite and opt-in PostgreSQL integration tests. Only controlled PostgreSQL overlap tests
establish the named locking guarantees; browser and API journeys alone do not. No mock test
proves real AI quality. Capture failed evidence as well as successes; revalidate completion against
every acceptance criterion before closing this plan.

## Risks
Provider charges require authority. Existing synthetic JWT configuration and dev servers are
not a production deployment. Parallel writes, stale responses, incomplete usage records and
invalid evaluation metrics remain material release risks. Do not overwrite pre-existing tickets.

## Progress
- 2026-09-08 reusable built-web verifier added to local runner/CI; 26 tooling tests pass. Live
  run failed one of 27 browser checks and preserved logs/trace with successful temporary cleanup.
  Exposed timestamp-dependent graph order: detection executed first but sorts after classification.
  Next action is [explicit step ordering](../completed/graph-step-ordering.md), keeping browser assertions
  unchanged. This harness is not verified green; broader production completion remains unproven.
- 2026-09-08 optional built-web runtime implemented: compiled same-origin frontend served by
  existing backend dependencies, production default and UID 10001 without Node/npm. Ruff and
  37 backend tests pass; 27 browser checks pass in explicit production mode, then four pass on
  final default-production image. Missing signing-key startup is rejected; runtime logs are
  clean. Separate migration/runbook documented, temporary container removed. See
  [evidence](../../testing.md#built-web-runtime). Add optional image verification to hosted CI
  when authorized; TLS/secrets/recovery and default-development-profile limits remain open.
- 2026-09-08 JSONL message types repaired after four silent-coercion reproductions. Non-string
  content now returns typed errors without partial examples or private value echo; numeric
  strings with declared language remain valid. Ruff and 40 affected tests pass; rebuilt live
  API verifies four 400 errors and a preserved 201 numeric-string import. No browser rerun.
  [Evidence](../../testing.md#jsonl-message-type-validation).
- 2026-09-08 malformed CSV quoting repaired after two accepted-invalid-input reproductions.
  Strict parsing now returns typed errors without private text or partial examples; valid
  multiline/comma/escaped-quote content remains accepted. Ruff and 36 affected tests pass;
  rebuilt live API verifies 400/400/201 and preserved content. No browser change or rerun.
  [Evidence](../../testing.md#strict-csv-quoting-validation).
- 2026-09-08 evaluation resource isolation verified with valid foreign evaluation/folder IDs
  and an owner of both workspaces. Eighteen requests reject before disclosure/mutation/model
  dispatch; correct-scope reads succeed and snapshots remain unchanged. Ruff and 28 affected
  tests pass; no application change or browser rerun. See
  [evidence](../../testing.md#evaluation-resource-workspace-isolation). Concurrent folder/resource
  races and other resource permission matrices remain open.
- 2026-09-08 unexpected evaluation failures now roll back unfinished writes and attempt a failed
  terminal outcome, retaining committed results/usage and re-raising original errors. Secondary
  persistence failures emit content-free correlated diagnostics. Ruff and 32 tests pass, four
  browser checks pass, 543 HTTP outcomes have no server/errors. Evaluator baseline lowered to
  479 lines. [Evidence](../../testing.md#evaluation-terminal-failures). Process-crash and
  persistent-outage recovery remain required; no replay/resume behavior was added.
- 2026-09-08 running evaluation deletion repaired after API/PostgreSQL reproductions. Permanent
  deletion now returns 409 between model calls as well as during active reservations. Paused
  execution completes safely, then remains deletable. Ruff and 30 affected tests pass, four
  browser checks pass, 543 HTTP outcomes have no server/errors. Route baseline lowered to 322.
  [Evidence](../../testing.md#running-evaluation-deletion-protection). Orphaned-running recovery,
  cancellation and restart/resume remain release gaps; elapsed time cannot justify deletion.
- 2026-09-08 evaluation management audit atomicity repaired after three API reproductions.
  Extracted transaction owner, passed authenticated actors, preserved reservation deletion guard.
  Ruff and 28 tests pass with PostgreSQL visibility/rollback/retry; rebuilt API passes four
  multilingual browser checks, 543 HTTP outcomes without server/errors. Lowered evaluator/route
  baselines. [Evidence](../../testing.md#evaluation-management-audit-atomicity). Full release
  remains open: continue permission/resource races, AI quality and process recovery work.
- 2026-09-08 evaluation management authorization verified: six actor cases cover 26 denied
  requests before service entry, no disclosures and unchanged evaluation/accounting/audit rows.
  Ruff and 26 affected tests pass; no application change or browser rerun. See
  [evidence](../../testing.md#evaluation-management-authorization). Next reliability target:
  reproduce and repair evaluation move/archive/delete committing before their audit records.
- 2026-09-08 full verification resumed: 572 backend tests pass with PostgreSQL, 22 tooling tests,
  lint, frontend build/types, audit and HTTP privacy pass. Full run passed 15/16 gates; notification
  trace showed a still-running refresh at the toast assertion deadline. Test now waits boundedly
  for operation completion before unchanged toast/fade assertions. All 27 browser tests then
  pass at ten workers, no retries; runtime windows have zero server/errors. Exact evidence and
  remaining latency limits: [testing](../../testing.md#full-regression-and-refresh-completion).
  This is a verification/harness increment, not production completion. Continue with remaining
  permission, AI-quality and recovery gaps; do not repeat unchanged backend tests for this test edit.
- 2026-09-08 Uvicorn access-log privacy leak reproduced with synthetic path/query marker.
  Disabled duplicate raw access records and added a live correlated-outcome privacy gate to
  local runner/browser CI. Rebuilt API passes; all 22 tooling tests pass, with PowerShell syntax
  and repository checks. Full pipeline now has 16 normal gates but has not been rerun; hosted CI,
  traceback sanitization and retention remain open.
- 2026-09-08 CSV shape handling repaired after reproducing an extra-field exception and silent
  data loss from duplicate headers. Typed errors preserve failed batch without partial examples;
  quoted multiline content stays valid. Ruff and 33 tests pass; rebuilt live API probe returns
  400/400/201 as expected. No browser change or rerun.
- 2026-09-08 explicit per-conversation language added to CSV/JSONL imports after six failures
  reproduced ignored annotations. Preserves declared EN/JA/ZH, including kanji-only Japanese;
  validates annotations before example persistence. Ruff and 47 tests pass, four browser checks
  pass, 543 HTTP outcomes have no errors. Caller metadata is not language-quality verification.
- 2026-09-08 numeric/emoji replies now inherit their own detected conversation language during
  dataset import. Three EN/JA/ZH failures reproduced first; unsupported alphabetic content and
  conversations without a language signal remain rejected without partial rows. Language
  preparation extracted to a focused helper. Ruff and 35 tests pass; four browser checks pass;
  543 HTTP outcomes have no server errors. Heuristic language detection limitations remain.
- 2026-09-08 human label concurrency repaired after two PostgreSQL reproductions. Scoped
  conversation locking and refreshed labels protect first creation and stale-value updates.
  Ruff and 38 tests pass; four browser checks pass; 543 HTTP outcomes have no server errors.
  Current last-writer-wins semantics remain; audit/history, conflict UI and deletion races are separate.
- 2026-09-08 dataset permission verification expanded with six actors and 25 denied requests,
  including reviewer reads and human-label replacement. Real dependencies stop service entry;
  full dataset/conversation/label/audit snapshots remain unchanged. Ruff and 32 affected tests
  pass in 15.42s. No application changes or browser rerun; complete role/resource matrix remains open.
- 2026-09-08 dataset move/delete audit atomicity repaired after two reproduced partial writes.
  Actor-attributed audit commits with mutation; PostgreSQL tests preserve dataset and child rows
  on failure and permit retry. Ruff and 31 tests pass; four browser checks pass; 543 HTTP outcomes
  contain no server errors. Import/label audit coverage and concurrent editing remain separate.
- 2026-09-08 dataset partial-import defect reproduced in three late-language-failure cases.
  Validate all languages before inserting examples/messages/labels; preserve failed batch and
  empty dataset, existing rows and corrected retry. Ruff and 27 tests pass; four browser checks
  pass; 543 HTTP outcomes have no server errors. Dataset move/delete audit commits remain
  separate and need transaction repair; language inference policy and database failures are unchanged.
- 2026-09-08 complete verification after knowledge integrity repairs: all 15 runner gates pass
  in `.artifacts/20260907T205147063Z`. Backend 535 tests (PostgreSQL enabled), browser 27 tests,
  tooling 19, lint/build/audit, startup/readiness and migration 0030 pass. Runtime review finds
  2,583 HTTP outcomes with zero server/error outcomes. No source edits during execution or
  retries; ten browser workers unchanged. This replaces the older full baseline, while real AI
  quality, remaining permission/resource coverage, production deadlines and recovery stay open.
- 2026-09-08 concurrent reindex version collision reproduced and repaired through scoped
  NO KEY UPDATE and fresh ORM state before mutation/version allocation. Controlled PostgreSQL
  overlap yields successful versions 2/3 and preserved newer metadata. Ruff and 46 tests pass;
  four browser checks pass; 543 HTTP outcomes have no server/error outcomes. Document lock spans
  provider work; production deadlines and crash recovery remain separate work.
- 2026-09-08 knowledge audit repair completed for upload/reindex as well as move/delete.
  PostgreSQL proves publication rollback and retained independently recorded embedding usage.
  Ruff and 45 tests pass; 12 browser checks pass; 1,238 HTTP outcomes contain no server errors.
  Failed provider status/accounting remains explicit. Concurrent reindex serialization and
  durable recovery remain separate gaps; see the completed knowledge audit plan.
- 2026-09-08 document move/delete audit atomicity repaired after two reproduced failures.
  Service-owned transaction includes index deletion and attributable audit; PostgreSQL visibility
  and retry checks pass. Ruff and 37 tests pass; four browser checks pass; 543 HTTP outcomes have
  no server/error outcomes. Upload/reindex audit publication remains the next step in
  [knowledge audit atomicity](../completed/knowledge-audit-atomicity.md), subsequently completed.
- 2026-09-08 knowledge management denial verified: six actor cases, 19 rejected writes,
  no service entry and unchanged indexed data/usage/audits. Ruff and 38 affected tests pass.
  Existing successful management and foreign-workspace checks remain green. Authorized document
  mutation and audit commits are still separate; failure atomicity needs a dedicated inspection.
- 2026-09-08 client-visible failure references completed after review: generic unexpected-error
  response and CORS exposure, UUID display, preserved session/draft and explicit retry. Ruff and
  25 backend regressions pass; saved full browser suite passes 27 checks; retained API logs have
  2,525 HTTP outcomes with zero server/error outcomes. No-store and original-exception propagation
  are regression-protected. Global log redaction and durable failure recovery remain open.
- 2026-09-08: [request-to-graph correlation](../completed/request-graph-correlation.md) verified
  through 29 affected backend tests, seven browser checks and 18 live persisted trace matches.
  Runtime: 591 HTTP outcomes without server/error outcomes. No frontend or migration change.
- 2026-09-08: [refresh reliability](../completed/refresh-verification-reliability.md) repairs
  repeated full-suite failures through grouped catalog queries and action-triggered session
  rejection. All 15 pipeline gates pass: 507 backend tests, 26 browser checks, 19 tooling
  tests, lint/build/types, migration 0030 and audit. Runtime: 2,519 HTTP outcomes, no failures.
  Guardrail timing improved in-suite; latency SLA, real-provider quality and recovery remain open.
- 2026-09-08: [atomic folder audit](../completed/folder-audit-atomicity.md) repairs changes
  surviving failed audit writes. Three failing reproductions; 43 affected tests including
  five PostgreSQL cases and five browser checks pass. Runtime: 482 HTTP outcomes without
  server/error outcomes. Resource assignment/deletion races and uncertain commits remain open.
- 2026-09-08: [folder cycle integrity](../completed/folder-cycle-integrity.md) prevents descendant
  and concurrent opposing moves from creating cycles. Reproductions fail before the fix;
  37 affected backend tests, two with PostgreSQL, and three browser checks pass. Runtime:
  235 HTTP outcomes, zero server/error outcomes. Fresh-state regression covers restoring a
  former parent. Existing data repair and resource deletion/assignment races remain open.
- 2026-09-08: repaired name-only folder PATCH unexpectedly clearing the parent. Four failing
  regressions reproduced it; 38 backend tests, five browser checks, lint/build/types and
  repository gates pass. Browser rename sends only the name. Runtime: 482 HTTP outcomes,
  no server/error outcomes. See [evidence](../../testing.md#folder-patch-preserves-hierarchy).
  Cycle prevention and concurrent hierarchy/audit integrity remain unverified.
- 2026-09-08: [folder mutation authorization](../completed/folder-authorization-boundary.md)
  adds 16 populated-fixture denial cases before service entry with unchanged folder/audit state.
  All 34 affected API tests and lint pass. No runtime defect exposed; full management coverage,
  hierarchy integrity and concurrent mutation/audit behavior remain separate work.
- 2026-09-08: [explicit support language](../completed/explicit-support-language.md) verified.
  Kanji-only Japanese can be selected explicitly; evaluation preserves declared case language.
  Full backend lint/474 tests, 25 browser checks, build/types and 19 tooling tests pass.
  Corrected API: 2,291 HTTP outcomes, no server/error outcomes. Prior notification timing
  failure passed unchanged; investigate refresh latency separately, without erasing its trace.
2026-09-08 answer-language repair: reproduced eight guardrail/evaluation failures caused by
citation titles. A focused core helper excludes exact known chunk references before detecting
answer prose language; citation-only output cannot pass. Unknown references and malformed/empty
packed sources are not stripped. Guardrail and evaluation consumers share the helper; evaluation
runner remains at its existing size baseline. Verification: 69 backend tests, lint, seven
multilingual checks and a live cross-language-title workflow/evaluation passed; runtime review
shows 598 HTTP outcomes with zero server failures. Evidence: [answer language](../../testing.md#answer-language-excludes-citation-metadata).
Kanji-only input ambiguity remains a separate gap; full goal stays active.

2026-09-08 archived retrieval admission completed: shared permission dependency now supports an
active-workspace requirement for execution-bearing reads, applied to new retrieval searches.
Reproduced archive bypass for owner/viewer/reviewer; denial now precedes retrieval and leaves
ledgers unchanged. History reads and restored execution pass. Verification: 45 backend tests,
four PostgreSQL-only skips, lint, nine live checks plus explicit HTTP archive/restore probe;
753 HTTP outcomes with zero server failures and repository gates. See
[archive admission](../../testing.md#archived-retrieval-admission). In-flight cancellation and
broader release requirements remain open; goal remains active.

2026-09-08 planned archive admission repair: retrieval/search currently inherits knowledge:read
and can execute after workspace archive. Add a requires-active option to the shared permission
dependency for execution-bearing reads; apply it only to new retrieval search, preserving trace
inspection and existing role access. Test owner/viewer/reviewer archive denial before retrieval,
unchanged ledgers, historical trace reads, and restored execution. Archive is an admission
boundary, not cancellation of already-running calls; concurrent archival cancellation is out of
scope. No schema changes or permission expansion.

2026-09-08 local network boundary completed: four wildcard host publishers changed to explicit
127.0.0.1 bindings. Resolved config and live Docker publisher checks pass; PostgreSQL volume and
migration head retained. All 24 browser tests pass in 57.1s; runtime review shows 2,215 HTTP
outcomes and zero server failures. [Evidence](../../testing.md#local-loopback-network-boundary).
No application code changed. Local processes/containers, deployment secrets, TLS and controlled
remote access remain separate concerns; full production objective remains active.

2026-09-08 planned local network boundary: live Docker publishers show API/frontend/PostgreSQL/
Redis on both 0.0.0.0 and IPv6 wildcard. Restrict the local Compose profile to IPv4 loopback,
keeping service-to-service networking and localhost developer access. Recreate only the isolated
stack, retain the PostgreSQL volume, verify resolved/published bindings and browser workflows.
This removes default LAN exposure; it does not replace secrets, TLS or production networking.

2026-09-08 full regression completed after citation/review and restore work: all 15 checks pass
in `.artifacts/20260907T181501351Z/`, with 450 backend, 24 browser and 19 tooling tests; lint,
frontend build/types, audit, startup and migration head 0030 pass. No retry or application change
during the run. Logs: 2,222 HTTP outcomes, zero server failures; live mock/no-key isolation
confirmed. See [full regression](../../testing.md#complete-regression-after-citation-and-recovery-work).
Next release work must address real answer-quality evidence, crash/restart behavior and remaining
permission/deployment gaps; this green run does not close those requirements or the full goal.

2026-09-08 restored application verification completed: extended the disposable restore drill
with a separate API process using normal dependencies and restored PostgreSQL data. EN/JA/ZH
original login, retained reads/traces/costs, permission denial and new cited runs pass. Source
fingerprints stay unchanged; target cleanup and normal API health pass. Evidence: 33 HTTP
outcomes, zero server failures, 19 tooling tests; [restored operation](../../testing.md#restored-application-operation).
An evaluation-list fixture assumption failed on the first attempt and was corrected with its
failed evidence retained. This does not prove network/browser cutover or crash recovery.

2026-09-08 local restore drill completed: added binary-safe pg_dump/pg_restore orchestration,
all-public-table fingerprints, failure reports and generated-target-only cleanup. Live restore
matched 36 populated tables and migration 0030 in 9.735s; independent cleanup query and source
API health passed. All 19 tooling tests pass, including failure/cleanup cases. See
[local database restore](../../testing.md#local-database-restore). Application cutover, external
backup operations and recovery objectives remain unverified; broader goal stays active.

2026-09-08 planned local database restore drill: add a stdlib-only script dedicated to the
synthetic asi-verification PostgreSQL service. Dump to ignored artifacts, restore into a unique
new database, compare complete public-table counts/content fingerprints and Alembic revision.
Require unchanged source manifests before/after dump; fail explicitly on concurrent changes.
Cleanup only the created target. Preserve archive/report evidence. No application data reset,
production backup policy, disaster simulation, automated scheduling or RPO/RTO guarantee.

2026-09-08 review-answer repair completed: reproduced five invalid publications and added a
focused validator before mutation. Blank or invalid canonical references cannot publish; safe
uncited human responses remain allowed. Added 16 API cases including foreign/malformed/failed
snapshots and correction without partial state. Service baseline lowered 316 to 312 lines.
Final evidence: 48 backend tests including PostgreSQL transitions, lint, 11 browser checks,
990 HTTP outcomes with zero server failures, repository gates. See
[review answer integrity](../../testing.md#human-review-answer-integrity). Full goal remains open.

2026-09-08 planned review-answer integrity repair: approval/edit must reject blank answers and
canonical chunk references absent from the run's successful packed evidence. Preserve uncited
human-authored safe responses and rejection. A focused helper owns validation before review
mutation; existing row locks/atomic commit remain. Test valid/mixed/missing evidence, denial
without mutation, then successful correction. No schema migration or paid provider calls.
Compatibility: legacy cited drafts lacking packed evidence must be edited or rejected.

2026-09-08: resumed the full objective after the documentation-only audit. Reproduced and fixed
vector-RAG evaluation accepting mixed valid/invented citations by reusing the shared validator.
Candidate text and accounting remain inspectable; invalid references produce the review outcome
with no accepted citations. Verification: 58 focused backend tests, full backend lint, seven
live multilingual checks, repository gates; 591 HTTP outcomes with zero server failures.
Evidence and exact limits: [evaluation citation integrity](../../testing.md#evaluation-citation-integrity).
Factual entailment, real-provider quality and the broader release requirements remain open.

2026-09-08: corrected evaluation failure usage reporting. Direct/vector provider overrun errors
now retain attached ledger tokens/cost in result metrics without publishing the rejected answer.
The pre-fix image reproduced 5 reported prompt tokens versus 4,000 in the ledger. Focused
evaluation validation passes 36 tests; see [evidence](../../testing.md#evaluation-failure-usage).

2026-09-08: closed direct/vector baseline model admission bypass with migration 0030, shared
monthly reservations and per-evaluation baseline usage. Verified 427 backend and 24 browser
tests, PostgreSQL overlap/rollback and lint. See
[evaluation admission](../completed/evaluation-budget-admission.md). Separate graph/embedding
limits, exact external billing and durable recovery remain explicit limitations.

2026-09-08: expanded real viewer/reviewer browser coverage with forged denied mutations,
foreign document/search IDs, usage invariance and permitted reviewer rejection. All 24 browser
tests and seven backend execution-spy denial tests pass. See
[restricted-role plan](../completed/restricted-role-browser.md). Application code unchanged;
complete role-by-route coverage and real AI quality remain open.

2026-09-08: repaired invalid-session startup and disabled bootstrap retry. Extracted typed HTTP
transport with generation-bound expiration; background reads report failures. All 22 browser
tests and frontend/tooling gates pass. See [session recovery](../completed/session-recovery.md)
and [test evidence](../../testing.md#session-recovery). No backend source changed.

2026-09-08: resumed implementation after the scoped documentation pass. Reproduced and repaired
frontend workspace/session response leakage; root generation guards also reject stale callbacks
after returning to the same workspace. All 15 browser tests and frontend/tooling gates pass.
See [completed isolation plan](../completed/workspace-response-isolation.md) and
[test evidence](../../testing.md#workspace-response-isolation). No backend code changed.

2026-09-08 complete local runner passes: all 15 checks in
`.artifacts/20260907T162849956Z/checks.json`, including 415 backend and 12 browser tests.
Manual runtime review found zero server failures across 790 HTTP outcomes. Provider isolation
and caller-setting restoration were verified. This closes the current complete-runner evidence
gap. Keep the broader goal active: denied-role/resource management, factual/semantic quality,
deployment recovery, hosted CI and architectural constraints still need their own proof.
2026-09-08 complete-runner verification: execute all current checks together from the rebuilt
isolated stack, retaining timestamped results. Inspect found that the runner did not override
embedding provider selection and linted less than CI. It now forces mock embeddings, restores
the caller's provider afterward, and runs `ruff check .` including migrations. The first run
uses parent EMBEDDING_PROVIDER=openai to verify isolation. This checks the local harness;
hosted CI, deployment recovery and real AI-quality evidence remain separate acceptance items.
Two full runs exposed the migration import grouping missed by the prior app/tests-only lint.
The second change fixed ordering but missed the required group separator. Inspected Ruff's
exact diff and verified a focused lint preflight before the next full run. The runner now emits
lint results before the backend suite and keeps runtime logs in artifacts without flooding
console output. All failed runs remain in `.artifacts/20260907T161722518Z/` and
`.artifacts/20260907T162255221Z/`; do not describe either as a complete passing verification.
- 2026-09-08: graph query embeddings now enforce agent/per-run budgets and carry run/step ledger
  links. Denied calls skip dispatch; expected provider failures retain uncertainty and route to
  review with failed graph/tool evidence. Extracted the retrieval node; graph runner is 627 lines.
  Full backend passes 378 tests, ten browser tests pass on rebuilt API, and final lint/gates pass.
  Continue operator reconciliation and controlled real quality evidence in
  [semantic retrieval](semantic-retrieval.md).
- 2026-09-08: configured OpenAI embeddings now run through document indexing and retrieval with
  independent ledger admission, shared settings and bounded batches. Synthetic EN/JA/ZH API
  integration verifies permissions and persistence. Full backend passes 369 tests; rebuilt API
  applies 0027/0028, and ten browser tests pass in default mock mode. Knowledge management is
  under 300 lines after indexing/contracts extraction. Continue graph attribution/per-run embedding
  budgets and real quality verification in [semantic retrieval](semantic-retrieval.md).
- 2026-09-07: durable embedding admission and accounted provider pass PostgreSQL transaction,
  budget concurrency and migration checks. Fixed an observed FK lock conflict and dataset
  pagination tie; made four chronological pagination fixtures deterministic. Final backend suite
  passes 356 tests, lint and repository gates pass. Provider runtime wiring remains open in
  [semantic retrieval](semantic-retrieval.md); no paid provider calls were made.
- 2026-09-07: added a validated embedding API boundary with 30 passing synthetic API/transport
  tests and passing lint. It remains disconnected from application dispatch until durable
  accounting/admission is implemented; see [semantic retrieval](semantic-retrieval.md).
- 2026-09-07: embedding storage now permits semantic dimensions via revision 0027. PostgreSQL
  tests prove value preservation and explicit unsafe-downgrade refusal; 33 affected tests pass.
  Continue the [semantic retrieval plan](semantic-retrieval.md) with accounted provider integration.
- 2026-09-07: vector retrieval now excludes incompatible provider/model embeddings and rejects
  malformed query/stored vectors before scoring. Full backend suite passes 318 tests; lint passes.
  Continue [semantic retrieval](semantic-retrieval.md) for storage, accounted provider integration
  and real quality evidence. This compatibility repair does not close AI-quality release gaps.
- 2026-09-07: default mock retrieval now uses lexical relevance, including conservative English
  plurals. Synthetic vectors no longer inflate relevance. 309 backend and ten browser tests pass;
  live verification also repaired unhandled workspace refresh rejection with visible error/retry.
  See [retrieval evidence](../completed/mock-retrieval-relevance.md). Semantic retrieval remains open.
- 2026-09-07: repaired citation guardrails that accepted retrieval metadata without answer
  references. Uncited EN/JA/ZH responses now route to review under default policy. 301 backend
  tests and nine live journeys pass; see [citation validation](../completed/answer-citation-validation.md).
- 2026-09-07: workflow authorization matrix passes with real permission dependencies, execution
  spies and unchanged ledgers. Thirteen affected tests and final lint pass; no application defect
  found in this scope. See [authorization evidence](../completed/workflow-authorization.md).
- 2026-09-07: complete EN/JA/ZH browser journeys pass after repairing the post-import React crash
  and late navigation away from review. Nine Playwright tests and frontend build pass; see
  [browser acceptance](../completed/multilingual-browser-acceptance.md). Mock AI quality limits remain.
- 2026-09-07: inspected architecture; added code map/local guides and production audit.
- Added source-size guardrail, request outcome logging and the Windows verification runner.
- Repaired folder-control accessibility, toast regression timing and agent-draft overwrite.
- Full local run `.artifacts/20260907T101634809Z/`: all 14 checks pass, 197 backend tests,
  3 browser journeys, 13 tooling tests, lint/build/audit/startup/readiness and log capture.
- Repeated browser regression previously passed 9/9; old-shell regression fails as expected.
- Browser CI job defined locally; remote execution/required checks remain unverified.
- Signing-key configuration guard completed with startup probes, 22 final focused tests and
  backend regression/lint evidence; see the completed signing-configuration plan.
- Fixed retrieval of obsolete document versions: EN/JA/ZH regressions fail before the fix;
  49 affected tests and live PostgreSQL API probes pass afterward. Historical versions retained.
- Direct evaluation now honors configured providers; success/failure/accounting/isolation tests
  and the live browser evaluation/review journey pass.
- Replaced canned RAG answers with vector-only retrieval, bounded evidence generation and ledger
  accounting. 50 affected tests, seven final focused cases and three browser journeys pass.
  Factual support grading remains a P1 gap. The completed metric contract removes the misleading
  grounding label; affected tests/build/browser and final lint pass.

## Decisions
- Agent budget admission is now integrated and verified: 277 backend tests, three browser
  journeys, migration 0026 and lint pass. Non-agent evaluation admission and exact provider
  billing remain outside that repair. Next verify the complete EN/JA/ZH user journey.
- Atomic review transitions completed: 239 backend tests including five PostgreSQL cases,
  three browser journeys and lint pass. Subsequent graph outcome publication now stages final
  guardrails and queue insertion with run status; failure-injection and PostgreSQL visibility
  checks pass. Process-crash recovery and persistent database outages remain open.
Use current code evidence over historical completion labels. Preserve original failed runs.
Keep existing incomplete Linux backend `.venv`; Windows validation uses disposable Docker runs.
Small scoped automation does not authorize commits or publication. Maintain documentation in
focused owners and active/completed plans rather than another repeated instruction manual.

## Findings
The saved multilingual API failure exposed canned mock policy answers, now repaired by bounded
source excerpts with exact citations. All three HTTP journeys pass through review, evaluation,
cost and workspace resource checks. See [testing](../../testing.md#multilingual-policy-repair-verification)
for the earlier backend/API checks. Subsequent multilingual browser acceptance now passes nine
Playwright tests. Complete denied-role journeys and real AI quality remain unproven; simulation
excerpts do not close those requirements.

Mock embeddings, evaluation validity, exact billing, durable recovery,
production credentials and large-module coupling remain open. An intermediate evaluation setup
socket hang-up has no established cause; retain its evidence and investigate if reproduced.

## Final Result
Open. The local verification loop works; the complete production acceptance criteria are unmet.
