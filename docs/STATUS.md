# Current status

Goal: **M1–M6 active and incomplete; resumed by the user on 2026-09-09**.
Current implementation slice: M3 abandoned retrieval accounting; M2 release gaps remain open. On 2026-09-09 the user authorized an independent documentation audit,
corrections and the [documentation freshness harness](plans/completed/documentation-freshness.md).
Those bounded tooling tasks did not resume application work; the subsequent app-goal resume did.
The harness now provides generated source references, six source/document review mappings and
CI freshness checks. [The protocol](DOC_FRESHNESS.md) distinguishes review attestations from
semantic proof; a weekly Codex gardening task is configured separately from application work.
The user also approved synchronizing the [reusable goal](REBUILD_GOAL.md) with development
provider and documentation-workflow clarifications; it is now covered by project freshness checks.
The [documentation reconciliation record](plans/completed/2026-09-09-documentation-reconciliation.md)
tracks the independent findings and maintenance lessons separately from application progress.
Branch: `codex/fresh-start`. Goal starting revision: `2c292d08b5ff9d577276c8513fc53582a1ba93d4`.
[M3 recovery plan](plans/active/m3-retrieval-recovery.md) owns current implementation;
[M3 linked-attempt record](plans/completed/m3-linked-attempts.md) retains the preceding slice;
[M3 review record](plans/completed/m3-human-review.md) retains review decisions/evidence;
[M2 execution plan](plans/active/m2-real-retrieval.md) retains retrieval decisions and evidence;
[M1 history](plans/active/m1-foundation.md) retains foundation work.
Normal verified commits/pushes to this branch are authorized. No merge/deploy/paid API authority.
The new work window starts **2026-09-09 00:44:58 UTC** and ends **04:44:58 UTC**
(13:44:58 Tokyo time), retaining the four-hour limit. Previous cutoff/evidence remain historical.

## Verified current behavior

The human-review slice has verified distinct execution/outcome fields, immutable review decisions,
operator/admin enforcement, durable review continuation and connected approve/edit/reject controls.
Linked attempts have database and browser evidence. M3 remains incomplete: remaining routing
and broader recovery are required.
The detailed failure and repair record belongs to the M3 plan.

- Real login, sessions, workspace roles and server-enforced permissions.
- PostgreSQL jobs with claims, leases, cancellation and fenced publication; one worker.
- TXT/Markdown originals, versions, bounded background indexing, withdrawal and restore.
- Real pinned local CPU embeddings and PostgreSQL/pgvector retrieval, followed by a measured
  local multilingual reranker over 20 authorized candidates. No external API needed for search.
- Knowledge upload/search/source inspection UI, including exact cited versions and offsets.
- Persisted model identity, status, locally counted tokens, duration and zero external charge.
- The UI labels **responses** as simulated; retrieval is real.
- Support API stores original messages and runs, executes a real persisted LangGraph, releases
  the worker at a development handoff, and resumes into an exact-source cited draft.
- Run-level cancellation, requester/contributor checks and current-source validation protect
  resume/publication. Clarification and insufficient evidence are separate terminal outcomes.
- Connected workbench: searchable paginated messages, selected original/draft, exact citations,
  expandable graph/model records, cancellation and admin development-response controls.
- Review preserves original drafts/citations and stores a separate final response; policy exceptions
  and unclassified legacy drafts require admin approval. Viewer inspection is read-only.
- Linked clarification/retry creates fresh processing under current authority; original messages,
  earlier inputs/results and decisions stay available in bounded history.

## September 9 linked-attempt evidence

Built on `497b160`; migration `0009_attempts` ran in the isolated four-service runtime.
- 91 PostgreSQL tests passed in 161.33s against an unchanged snapshot:
  `.artifacts/m0/integration-20260909T031006335983Z`.
- `.artifacts/m3/linked-attempt-ui`: seven browser cases passed; the viewer case failed because
  it assumed an old unreviewed draft was on the first page. The test now creates its own draft.
- `.artifacts/m3/linked-attempt-ui-repaired`: both affected viewer and linked-attempt cases passed.
  Together these cover all eight journeys, not one fresh eight-case green run. The repaired
  viewer 360px source screenshot and linked history screenshot were inspected without overlap.
- Actual Chrome inspection confirmed the original `w`, cancelled clarification and current retry
  remain distinct in three-attempt history. Retrieval remains real; responses remain simulated.
- TypeScript/Vite build, five component tests and Ruff pass. The additional component case checks
  emoji/supplementary Chinese counting and prevents oversized clarification submission.
- Independent backend/UI review found and repaired application labels affecting input validation
  and a UTF-16/code-point limit mismatch. No remaining blocking findings in these bounded reviews.

The whole-repository database evidence fingerprint predates the subsequent frontend/test/docs
repairs; backend sources did not change afterward. The plan retains failed evidence and limits.

## September 9 retrieval-recovery evidence

- 100 PostgreSQL tests passed in 186.85s against an unchanged snapshot:
  `.artifacts/m0/integration-20260909T033616695185Z`. Includes real process termination, database
  session loss, late embedding/reranking results, cleanup fencing and concurrent/fair recovery.
- All eight browser journeys passed: `.artifacts/m3/recovery-workbench-ui` (1.8 minutes).
- 16 unit tests passed: `.artifacts/m0/backend-20260909T033312194706Z`; Ruff and formatting pass.
- Chrome run `7aee3f1a-94e2-4a18-bd71-505f8b1c53e4` reached development wait with actual local
  retrieval. UI accounting matched `.artifacts/m3/recovery-live-result.json`; the corresponding
  worker completion log was inspected. The replacement API/worker/frontend/database are healthy.
- Independent recovery review found no blocking issue. Query/TCP settings improve detection;
  they do not guarantee a platform-independent network timeout or prove CPU inference stopped.

The first expanded suite passed 99/100; cancellation setup did not obtain a usable handoff.
Stronger claim/HTTP preconditions now retain the diagnostic cause instead of a missing-key error.
The case and final suite pass, but the original intermittent cause remains unresolved. The
execution record retains that failure and an earlier child-fixture model-registration failure.

## September 9 human-review evidence

Built on pushed workbench `281b169` (CI `34301042398` passed). Migration `0008_reviews` ran in
the isolated runtime, preserving earlier drafts as unclassified and unapproved.
- 79 PostgreSQL tests passed: `.artifacts/m0/integration-20260909T023808458445Z`.
- 16 backend unit tests passed: `.artifacts/m0/backend-20260909T023856099226Z`.
- Seven browser journeys passed: `.artifacts/m3/review-ui-final`, including EN operator approval,
  JA editing, ZH rejection, administrator-only policy approval, draft-arrival/polling regression,
  source focus, viewer widths and cancellation. Desktop/narrow screenshots and the final 360px
  operator policy-exception review screen were inspected; no overflow/overlap found.
- Six baseline browser cases passed: `.artifacts/m3/baseline-final`, covering sessions,
  member permissions, workspace denial and persisted model-free clarification.
- TypeScript/Vite build, Ruff and four component tests passed. These are boundary checks,
  not the complete release acceptance matrix.
- Chrome run `a98f393d-1b37-453b-ab66-e3a1e938f6ae`: actual local retrieval and Codex-authored
  development response; saved review interrupt survived a real worker restart and browser approval.
  `.artifacts/m3/restart-review-result.json` confirms one decision/job and preserved draft/final.
- Independent backend/UI reviews found and corrected legacy-classification, failed-node recovery
  and empty editor initialization issues. Failed resumed tasks may report empty graph `next`;
  errors/interrupts and completed output are now checked explicitly.

The preceding broad run passed 74/76 but found missing indexed data and negative handoff elapsed
(-544.771ms). Their causes remain unresolved. Expanded indexing diagnostics retain job/time/source
state; reversed timestamps now explicitly report `clock_anomaly` with null elapsed and preserved
raw timestamps. A 1,200-sample, 61.68-second database-clock observation found no backward jump;
it does not exclude an intermittent adjustment outside that window. No scheduler/host-clock
change was made. Full failures and follow-up evidence remain in the M3 execution record.

## September 9 connected workbench evidence

Built on pushed backend checkpoint `8cff3bb87fbcf467519dfd164fc8ee3a159782be`;
CI `34298862586` passed. The rebuilt app uses typed run/handoff projections.
- Final PostgreSQL suite: 62 passed in `.artifacts/m0/integration-20260909T014243087341Z`.
- Workbench browser suite: 6 passed in `.artifacts/m2/workbench-ui-final`; EN/JA/ZH drafts,
  actual local retrieval, source/version navigation, cancellation, viewer denial, keyboard
  source focus, 360/768/1440px and doubled content size. Screenshots inspected.
- TypeScript/Vite build and 4 component tests passed. Baseline browser coverage now includes
  model-free persisted clarification. Its six-case run passed five but hit the existing admin
  login throttle; the missing admin case passed after verified expiry. Evidence:
  `.artifacts/m2/workbench-ci-path` and `.artifacts/m2/workbench-admin-after-expiry`.
  This is combined local evidence, not a single all-green six-case baseline run; fresh CI will
  run the full suite against its own isolated database.
- Chrome live interaction and screenshot capture now work: inspected the persisted Chinese
  draft, source and model details, and submitted `w`, which produced clarification.
- Independent review caught transient polling erasing an unfinished answer and a late POST
  navigating back after leaving; fixed and covered by regressions. Inbox status now refreshes
  when the selected run changes state.

One initial PostgreSQL run returned no claimable resume job (61 passed, 1 failed). The next run
did not reproduce it but exposed a diagnostic-helper mistake in an intentional empty-queue test;
that helper mistake is fixed. The final 62-test run passes. The original claim cause is still
unknown; failures and nonintrusive diagnostics remain in the M2 execution record.

## September 9 support backend evidence

Built on `c9e8fa1` (its CI `34296092492` passed). Migration `0007_support` and explicit
PostgreSQL checkpointer setup ran in the rebuilt four-service development stack.
- 62 real PostgreSQL tests passed: `.artifacts/m0/integration-20260909T010333128389Z`.
  Includes real graph replay, concurrency, cancellation, source changes and permission denial.
- 16 unit tests passed: `.artifacts/m0/backend-20260909T011540019960Z`.
- EN/JA/ZH actual API/worker/local-model runs reached cited drafts; retained artifacts are
  `.artifacts/m2/support-runtime-en.json`, `support-runtime-ja.json` and `support-runtime-zh.json`.
  Codex authored each development answer from its exported retrieval context; no expected
  evaluation answers or external generation API were used. This is workflow smoke evidence.
- Independent security review found checkpoint connection errors needed retry translation and
  failed retrieval records needed early run association. Both were fixed; expanded tests passed.
  Prior interrupted graph steps are now marked uncertain on a subsequent attempt.

At that backend checkpoint the workbench UI was not connected. Human review, full process-kill
recovery and semantic generation-quality gates remain incomplete. The table below is historical.

## September 8 historical verification

| Boundary | Evidence |
| --- | --- |
| Frozen retrieval | 26/26 evidence cases; 27/27 groups; EN 8/8, JA 9/9, ZH 9/9; warm p95 2.5 seconds; zero forbidden leaks; foreign request 404 |
| Backend | 16 unit tests and 45 real PostgreSQL tests pass |
| Harness | 19 preparation checks pass |
| Knowledge UI | Two real desktop/mobile journeys pass; source/search screenshots inspected |
| Frontend | TypeScript/build and two component tests pass; baseline browser suite also passed |
| Models | Explicit preparation/inference passed for both pinned local models |
| Graph prerequisite | Supported LangGraph/PostgreSQL interrupt and failed-node recovery passed after connection reconstruction; application workflow was pending then |
| Git/CI | September 8 application checkpoint `2379915bcee9a14c64739e28b19b81c021d322d7`; CI `34257383552` recorded successful |

Final stable retrieval evidence: `.artifacts/m2/retrieval-eval-20260908T170142Z`.
Final label/browser evidence: `.artifacts/m2/provider-label-rebuilt-ui`.
Detailed command artifacts and prior failures are retained in the M2 execution record.
LangGraph `1.2.11` and PostgreSQL checkpointer `3.1.2` are installed in the rebuilt runtime.
September 8 PostgreSQL evidence: `.artifacts/m0/integration-20260908T172545791661Z`.
The real retrieval smoke still passes after dependency installation; the full frozen quality
measurement above belongs to the earlier retrieval snapshot and was not rerun for this lock change.
No full production-readiness, generated-answer quality or completed release claim is supported.
These are retained results from September 8, not newly executed application tests or a live
service-health claim. The checkpoint record is `.artifacts/m2/unattended-resume-checkpoint.json`.

## Failures and limits

- Original multilingual ranking failed (20/26 cases); the unchanged frozen corpus now passes
  after measured reranking. This set was used during tuning, not held out for generalization.
- One revocation test failed initially. An indexed-source precondition was added; isolated
  and full stable reruns pass, but the original intermittent cause is not established.
- Early checks whose source files changed mid-run remain invalid as overall evidence even
  when individual tests passed. Final verification ran against an unchanged snapshot.
- Earlier Chrome screenshot attempts timed out; connected workbench interaction/capture now
  works. This does not establish completed release/demo coverage.
- Upstream AnyIO and model cache-argument deprecation warnings remain visible.
- Synchronous retrieval ownership/reconciliation passes focused crash/late-write and full-suite
  checks. Wider recovery gates and the earlier intermittent setup failures remain incomplete.
- The release plan's lexical/fusion requirement differs from the implemented vector-plus-reranker
  path; comparative evidence or an explicit scope decision remains outstanding.
- The connected development draft and human-review paths are implemented; imports, complete
  observability, comparative evaluation and restoration remain incomplete.

## Next connected slice

Human-review checkpoint `497b160` is committed/pushed; CI run `34304500162` passed, confirmed
through the OpenAI GitHub connector. The preceding workbench CI `34301042398` passed.
Linked-attempt checkpoint `2e2054f` is pushed; CI `34306686806` passed. Preparation passed
35 checks after staging the intended completed-plan move. Finish recovery documentation receipts
and checkpoint; then implement the remaining human request-for-clarification outcome with a
preserved draft and linked follow-up. The final recovery suite passed 100/100; earlier failure
causes remain explicitly unresolved in the execution record.
Human-review concurrency and a real
worker restart at its durable wait have passed; broader routing/recovery gates remain open.
Never import evaluation answers as runtime responses, invent API usage or equate exact citations
with semantic support. Continue into the planned human-review/recovery gates after this slice.
The user resumed this implementation window; missing APIs do not block real local search.
Current topology and implementation boundaries are in [architecture](ARCHITECTURE.md).

## Preserved history

The old implementation/data/services and archive branch remain untouched. Foundation and
knowledge milestones are documented in the owning execution records rather than repeated here.
Future work must revalidate live services before operating on them.
