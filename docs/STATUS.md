# Current status

Latest user direction on2026-09-09: **continue M1–M6, prioritize a working demo; defer RAG tuning**.
User resumed on 2026-09-09 at 10:58 UTC. This unattended window ends at 14:58 UTC
(23:58 Tokyo); the earlier 06:04:24–10:04:24 window is historical. Full goal remains incomplete.

Previous completed slice: [isolated restoration drill](plans/completed/m6-restore-drill.md),
committed/pushed as ece351d. Independent safety and documentation reviews passed; all 45 prep
checks passed at `.artifacts/m0/prep-20260909T095644938452Z`.
Evidence: `.artifacts/m6/restore-20260909T095111Z/report.json`, wrapper
`.artifacts/m0/restore-20260909T095110422764Z`. All 22 public tables and extension metadata match
the same exported backup snapshot; the schema has no public sequences. The disposable restored
database processed a fresh `w` through authenticated ASGI requests and the real worker/LangGraph:
clarification_needed, succeeded job, three checkpoints, zero model calls. Original runtime was
not redirected. This is not restored network/browser operation, inherited-job replay or RAG quality.
Approved-response copying is implemented and verified: [record](plans/completed/m4-approved-copy.md).
39 component tests/build pass; three real multilingual review journeys pass, plus a final
360/768/1440 Japanese layout journey. Independent frontend review found no actionable issue.
Copy checkpoint301e747 is pushed; GitHub CI34343861442 passed.
Latest completed slice: [built local release](plans/completed/m6-local-release.md).
Fresh release-up/model preparation and three final real browser journeys
pass; two real knowledge journeys pass. Evidence and failed checks are in the linked record.
52 backend unit tests pass. Full PostgreSQL run had143 passes and one pre-dispatch child timeout;
instrumented focused recovery run passes9 checks with the unchanged20-second dispatch limit.
Full rerun passes144 checks in360.11s at `.artifacts/m0/integration-20260909T113404211217Z`.
Release checkpoint49d2829 is pushed; GitHub CI34347103025 passed.46 prep checks passed at
`.artifacts/m0/prep-20260909T114259823684Z`.
The scoped js-yaml4.3.2 development dependency repair is pushed as b35214e;
GitHub CI34348039265 passed. Audit zero, generated API types unchanged,39 frontend tests/build pass.
Latest completed feature: [historical evaluation results in Quality](plans/completed/m5-historical-evaluations.md).
155 full PostgreSQL checks pass at `.artifacts/m0/integration-20260909T122535921561Z`;
65 backend units and42 frontend tests/build pass. Three real browser journeys pass in11.5s at
`.artifacts/m5/evaluation-browser-fixed-20260909`, including failed traces, workspace switch,
foreign denial, outage recovery and360/768/1440 layouts. The live synthetic report is registered
in its actual evaluation workspace; registration does not rerun retrieval or certify source facts.
Historical results are pushed as855d1e1; GitHub CI34351992984 passed;46 preparation checks pass at
`.artifacts/m0/prep-20260909T123445042611Z`. The
[five-session release profile](plans/completed/m6-small-team-profile.md) now passes against built
assets: five independent operator sessions inspect actual retrieval and cancel at development
handoff while real knowledge ingestion proceeds. Final browser evidence is
`.artifacts/m6/small-team-final-20260909`; database intervals confirm admitted-work overlap.
Five focused PostgreSQL measurement checks pass. Profile checkpoint48f9409 is pushed; independent
code/documentation review closed and46 preparation checks passed at
`.artifacts/m0/prep-20260909T130840658739Z`. Current: add the
[packaged release CI smoke](plans/active/m6-release-ci.md), reusing the existing no-API journey;
local baseline passes three checks in8.4s. Keep RAG tuning deferred; five retrieval strategies
do not complete EVAL and the workload profile does not exercise generation.
The previous [settings and usage slice](plans/completed/m4-settings-usage.md) is committed/pushed as
73e60a6;45 preparation checks pass at `.artifacts/m0/prep-20260909T094443836621Z`. Admin-only response-language
defaults and explicit provider configuration are implemented; Quality displays member-scoped
recorded model activity with unknown measurements retained. Migration0013 is applied and the
rebuild stack is healthy.18 focused PostgreSQL checks pass at
`.artifacts/m0/settings-usage-20260909T093847978612Z`;33 frontend tests and TypeScript/Vite pass.
Seven real browser journeys pass in25.5s at `.artifacts/m4/settings-usage-browser-20260909`,
including settings persistence, member access, session failures and360/768/1440 layouts. No external generation/API billing or evaluation-UI claim.

Import checkpoint a095a08 is pushed; GitHub CI34335092882 passed.45 prep checks passed at
`.artifacts/m0/prep-20260909T093003893465Z`. The completed import slice has141 full PostgreSQL
passes at `.artifacts/m0/integration-20260909T091937948269Z`,46 backend units,31 frontend tests
and two initial browser journeys plus one final styling journey. Chrome completed an imported
Japanese question through real retrieval, attributed draft and internal approval; records at
`.artifacts/m4/message-import-chrome-demo.json`. Full regression predates settings/usage.
The [import record](plans/completed/m4-message-import.md) retains review findings and failed evidence.

Prior comparison checkpoint f0b9f79 is pushed; GitHub CI34330562643 passed. Capacity tuning is
paused. Its five working files are preserved under
`.artifacts/rag-hardening/deferred-capacity-20260909`; runtime/tooling were restored to f0b9f79
before imports. The stress timeout and improved short-query timings belong only to that parked
experiment, not current production SQL. No50k-chunk capacity pass is claimed.
Dated sections below preserve prior checkpoints; current scope and next action above supersede them.

Latest checkpoint `3403d82` is pushed; GitHub CI `34329277751` passed. Preparation 40 passed at
`.artifacts/m0/prep-20260909T082745432597Z`. One shared frozen-corpus comparison completed at
`.artifacts/m2/strategy-comparison-20260909T083207Z/report.json`, with unchanged source/runtime.
Vector-rerank 26/26, hybrid-rerank 25/26, vector 22/26, BM25/hybrid 20/26 evidence cases. All five
pass leakage/foreign404 checks; only reranked methods pass the full frozen retrieval gate.
Default remains vector-rerank: hybrid loses a conflicting policy in Japanese case ja02 before
reranking. Warm p95:2.516s default and2.437s hybrid-rerank. No generation quality is claimed.
Post-run independent-review repair strengthens trace shape validation; 12 metric/freeze tests
and all 160 saved case/probe traces pass strict revalidation without replacing measured results.
At that checkpoint the next task was demo verification. Current work is listed above.

Current slice: five explicit retrieval strategies and bounded candidate traces are implemented.
Knowledge search and Workflow → Retrieve evidence expose actual vector/BM25/fusion/reranker/final
ranks and exact source links. BM25-only invokes no model; the message/default path remains
vector-rerank. Hybrid superiority and50k-chunk performance are not established.

Verification: initial29 focused PostgreSQL checks passed at
`.artifacts/m0/hybrid-strategies-20260909T080916720578Z`. Full suite ran130 passing and one failed
in305.67s at `.artifacts/m0/integration-20260909T081149738658Z`: recovery failure injection still
named the extracted function. Updating the hook, without changing assertions, gives15 focused
strategy/recovery passes at `.artifacts/m0/hybrid-strategies-fixed-20260909T081906294913Z`.
42 units pass at `.artifacts/m0/backend-20260909T081519680780Z`;27 frontend tests and build pass.
Two final browser journeys pass in18.0s at
`.artifacts/rag-hardening/strategy-browser-compact-20260909`, including360/768/1440 layouts
and five-candidate preview/full-list expansion. The preceding fixed run also passed in21.9s.
Initial browser timing/selector failures remain in the adjacent strategy-browser directory.
Independent reviews found and fixed lexical preflight ordering and running-trace wording.
Chrome also inspected the Japanese ERROR-8422 hybrid result and exact source offset7956.

Foundation checkpoint `b904b90` is pushed; GitHub CI `34326510482` passed. Migration0010 backfilled
1284 retained chunks; migration0011 adds stage records without reconstructing old history.
Runtime guards stop old writers before migrations; all four rebuild services are healthy after
startup. The retained pre-migration dump is not restoration proof. The subsequent comparison
and next capacity step are recorded above.

Latest repair: **repetitive-source provenance and context retention verified**. The position-carrying
LangChain adapter fixes ambiguous occurrences; packing retains later fitting top-five evidence.
39 unit checks pass (`.artifacts/m0/backend-20260909T072159482639Z`) and 116 PostgreSQL checks pass
(`.artifacts/m0/integration-20260909T071621876300Z`). Three real EN/JA/ZH boundary probes pass at
`.artifacts/rag-hardening/boundary-20260909T071922Z`; the unchanged long-policy corpus passes
26/26 evidence cases and 27/27 groups, warm p95 2.672s, at
`.artifacts/m2/retrieval-eval-20260909T072217Z`. Development generation remains unverified.
Independent code review found no blocker and its tokenizer-overhead coverage request was added.
Existing documents need normal versioned re-ingestion; no historical chunks were rewritten.
Repair checkpoint `ffc730a` is pushed; preparation 37 passed at
`.artifacts/m0/prep-20260909T072811123359Z`. Chrome opened the freshly indexed Japanese
Boundary-ja.txt version at offset 7956 after actual retrieval; the complete policy fact was visible.
Its GitHub CI `34324082636` passed.

Preceding application slice: **workflow inspection and 50,000-message stored-state capacity verified**.
UI checkpoint `bf983df` is pushed; GitHub CI `34319742288` passed. Response/Workflow/Sources/History
tabs preserve editing state; URL filters/page survive detail navigation, and cancellation remains
available from every tab. The table requests 20/50 rows and unmounts during detail inspection.

Capacity evidence: `.artifacts/m0/inbox-capacity-20260909T065459385520Z` has six passing checks,
including actual 50k-row browser navigation against a disposable API/Vite/database schema,
foreign-data denial and concurrent admission at the 50,000-message cap. First/deep/view/search
warm maxima were 65.7–234.1ms. Each case has only five warm samples (reported p95 equals maximum);
this proves bounded stored-state reads, not provider throughput, stable production latency or
50k successful AI runs. Initial latency failure 1007.1ms is retained at
`.artifacts/m0/inbox-capacity-20260909T064816811978Z`; the 1,000ms criterion stayed unchanged.
All-view paging/count and filtered latest-attempt anti-joins removed measured repeated work.

Full PostgreSQL regression: 116 passed in 291.36s
(`.artifacts/m0/integration-20260909T065711706876Z`). Backend unit checks: 24 passed
(`.artifacts/m0/backend-20260909T065810797302Z`), including real timeout/child cleanup.
Ruff and TypeScript/Vite build pass. The capacity checkpoint is pushed as `15e3218`; its
37-check preparation pass is `.artifacts/m0/prep-20260909T071037790250Z` after independent review;
GitHub CI `34322603929` passed.
The unchanged UI has 23 frontend tests, nine existing workbench journey passes in
`.artifacts/m4/workflow-inbox-ui-20260909`, and repaired inbox/workflow browser passes at 360/768/1440
in `.artifacts/m4/workflow-inbox-ui-fixed-20260909`. The initial mobile overflow failure remains
saved; source focus and viewer compose deep-link review findings were fixed with tests.
These checks do not establish full release or semantic RAG quality completion.

Preceding checkpoint: **RAG design audit and targeted repairs verified**; full hardening is incomplete.
[The execution record](plans/completed/rag-design-hardening.md) owns findings, repairs and verification.
This task started at 04:48:37 UTC with an 08:48:37 UTC stop limit. The preceding M1–M6 window
ended at 04:44:58 UTC; the audit itself did not resume the full release goal.
Preceding application checkpoint: M4 focused inbox views verified. On 2026-09-09 the user authorized an independent documentation audit,
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
[M4 inbox record](plans/completed/m4-inbox-views.md) owns the preceding app slice;
[M3 clarification plan](plans/completed/m3-review-clarification.md) retains the preceding checkpoint;
[M3 recovery plan](plans/completed/m3-retrieval-recovery.md) retains the preceding checkpoint;
[M3 linked-attempt record](plans/completed/m3-linked-attempts.md) retains the preceding slice;
[M3 review record](plans/completed/m3-human-review.md) retains review decisions/evidence;
[M2 execution plan](plans/active/m2-real-retrieval.md) retains retrieval decisions and evidence;
[M1 history](plans/active/m1-foundation.md) retains foundation work.
Normal verified commits/pushes to this branch are authorized. No merge/deploy/paid API authority.
The preceding app work window started **2026-09-09 00:44:58 UTC** and ended **04:44:58 UTC**
(13:44:58 Tokyo time), retaining the four-hour limit. Previous cutoff/evidence remain historical.

## Verified current behavior

The scoped [RAG audit](RAG.md) repaired artificial chunk-boundary evidence loss, sentence
separator placement and evaluator false positives. Fresh checks: 23 unit tests, 113 PostgreSQL
tests, three real EN/JA/ZH boundary probes, 26/26 frozen evidence cases (27/27 groups; warm p95
2.406s), and two knowledge browser journeys. See the linked execution record for artifacts and
remaining semantic/BM25/trace gates. Existing stored documents need versioned re-ingestion to
receive the chunk repair; no existing corpus or answer-quality threshold was weakened.

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

## Historical application checkpoint before the RAG audit

Human-review checkpoint `497b160` is committed/pushed; CI run `34304500162` passed, confirmed
through the OpenAI GitHub connector. The preceding workbench CI `34301042398` passed.
Linked-attempt checkpoint `2e2054f` and recovery checkpoint `13322ca` are pushed; their CI runs
`34306686806` and `34308144856` passed. Human clarification now passes 110 PostgreSQL tests
in 203.86s (`.artifacts/m0/integration-20260909T040250637259Z`), all nine browser journeys
(`.artifacts/m3/clarification-workbench-ui`), nine component tests and the TypeScript/Vite build.
Actual Chrome and stored records confirm a published question followed by fresh child retrieval
(`.artifacts/m3/clarification-live-result.json`). Clarification is pushed as `7c7abf3`; CI
`34310112516` passed, with 35 preparation checks and six independent documentation receipts.

M4 inbox views now pass 113 PostgreSQL tests in 217.67s
(`.artifacts/m0/integration-20260909T042732512966Z`), ten component tests and TypeScript/Vite.
The real inbox browser journey passes at 360/768/1440px
(`.artifacts/m4/inbox-views-ui-final`). The browser exposed and repaired mobile admin-navigation
overflow; independent review exposed and repaired pagination when filtered results shrink.
All nine existing workbench journeys also pass in 2.1 minutes
(`.artifacts/m4/inbox-workbench-regression`). Independent source and documentation reviews found
no remaining blocking issue after repairs. Checkpoint `8d7dd13` is pushed; CI `34311767057`
passed. Six independent receipts and 35 preparation checks passed
(`.artifacts/m0/prep-20260909T043813532131Z`). A final text-only repair removes misleading reply
guidance on historical clarification attempts; ten component tests and build pass afterward.
Full database/browser regression predates only that sentence removal and checkpoint docs.

That preceding four-hour window ended at 04:44:58 UTC (13:44:58 Tokyo). It is historical;
the resumed window and current next action at the top of this document supersede its stop limit.
On future resumes, inspect the current branch/CI, local processes and active record. The local ignored artifact
`.artifacts/m4/window-checkpoint.json` records final revision/CI observations when available;
absence on another checkout is not a failure. The full app goal remains incomplete.
The previously planned product slice was bounded
JSONL conversation imports with labels and an explicit selected-item
processing action, following REBUILD_PLAN. It remains deferred behind the current workflow/inbox
capacity priority linked at the top. Imports, lexical/fusion retrieval and other release
gates remain open; the current inbox query assumes each message already has a run, so imports
require a cohesive persistence/read-model change rather than bypassing the normal workflow.

The preceding full run had 105 passes and two setup failures. Database observations showed a
queued initial job 1.613051s ahead of a later clock reading. Tests now wait only for observed
initial-job availability, with a five-second bound and one worker execution. Production scheduling
and timestamps are unchanged. The passing final suite recorded only the synthetic 188ms wait;
the host/VM clock mechanism and causes of older intermittent failures remain unresolved.
Human-review concurrency and a real
worker restart at its durable wait have passed; broader routing/recovery gates remain open.
Never import evaluation answers as runtime responses, invent API usage or equate exact citations
with semantic support. Remaining human-review/recovery gates are release work, not audit completion.
Missing APIs do not block real local search.
Current topology and implementation boundaries are in [architecture](ARCHITECTURE.md).

## Preserved history

The old implementation/data/services and archive branch remain untouched. Foundation and
knowledge milestones are documented in the owning execution records rather than repeated here.
Future work must revalidate live services before operating on them.
