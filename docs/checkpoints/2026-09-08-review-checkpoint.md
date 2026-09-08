# CHECKPOINT — implementation paused, 2026-09-08

Created at the user's explicit stop request. No further implementation is authorized until review.
The already-started CPU profiling run finished normally; no test process from that operation remains
active. The local verification application was left in place. No commit, merge or deployment was made
as part of this checkpoint. Counts below describe the entire dirty worktree, not proven authorship.

## 1. Original goal

Build a reliable, production-minded local-first internal support intelligence platform for English,
Japanese and Chinese. The required journey is register/login → workspace → multilingual dataset import
→ knowledge upload → agent creation → grounded support response with citations → graph/retrieval/model
inspection → human review → evaluation → quality and cost inspection. Requirements include backend
permission enforcement before context access, workspace isolation, explicit failures, accounting,
recovery, reproducible startup and honest limitations. The full goal is NOT proven complete.

## 2. Work completed

Major areas represented by the current changes and recorded execution history:

- Agent-first documentation router, concise AGENTS.md, architecture/reliability contracts, quality
  score, persistent plans and subsystem guides; executable documentation and source-size gates.
- Permission-denial and cross-workspace coverage at workflow, resource and evaluation boundaries.
- PostgreSQL transaction/locking repairs for review publication, folders, labels, datasets,
  knowledge publication/reindexing, evaluation management and budget admission.
- Model reservations, accounted embedding requests, provider/configuration validation and uncertain
  usage preservation. Scoped owner-only embedding orphan recovery and separate billing confirmation.
- Explicit response language, citation/duration checks and review routing; retained graph sequencing.
- Evaluation baseline accounting, tested-expectation denominators, case prompt limits and comparison
  compatibility based on known scoring contract and loaded-case identity.
- Safe client failure references, HTTP/graph correlation and content-free server diagnostics.
- Browser session/workspace response isolation, agent draft preservation and Costs recovery controls.
- Local verification runner, browser CI definition, compiled non-root web/API image and restore drills.

These are implemented scopes with varying verification coverage, not a claim of full production readiness.
The latest addition is opt-in CPU profiling in the existing browser diagnostics fixture; it is diagnostic,
not a repair for the browser failure.

## 3. Change map

Inventory before adding this checkpoint: **312 files** = 74 modified tracked + 238 untracked.
No staged changes. Categories are mutually exclusive:

| Category | Files |
| --- | ---: |
| Application source (.py/.ts/.tsx/.css under backend/app or frontend/src) | 96 |
| Tests and test fixtures | 105 |
| Markdown documentation/instructions/plans | 85 |
| Alembic migration files | 7 |
| Tooling, configuration, dependency lock and runtime files | 19 |
| Total | 312 |

This checkpoint adds one Markdown file: final total **313**, docs **86**, untracked **239**.
Tooling scripts are in the 19-file category, not the 96 application-source count. Ignored runtime,
probe and trace artifacts are excluded. Exact pre-report paths/statuses are saved in
`.artifacts/checkpoint-change-inventory.json` (local ignored evidence).

## 4. Changes by subsystem

| Subsystem | Main changes |
| --- | --- |
| Auth | Production signing-key/environment validation; fresh membership checks for protected mutations; browser stale-session handling. No claim of an auth-system rewrite. |
| Database | Seven migrations; reservation tables/metadata, embedding dimensions/status, retrieval outcomes, evaluation reservations, graph ordering, execution ownership; scoped locks and atomic audit publication. |
| Retrieval | Configured accounted embeddings, compatible model/dimension checks, explicit retrieval failures/version handling, deterministic lexical mock behavior and shared cited-evidence validation. |
| Agent workflow | Extracted routing/retrieval/outcome/context helpers, admission accounting, language selection, explicit failure/review publication and persisted graph-step sequence. |
| Evaluation | Direct/RAG baseline execution, accounting and terminal failures; deletion/admission protection; expectation coverage, case limits and compatibility/provenance rules. |
| Observability | Request IDs, safe 500 references, server log formatting/privacy probes, graph correlation, ordered steps and browser transport/profiling diagnostics. |
| Frontend | Shared HTTP transport, workspace generation isolation, draft hook, run console, evaluation metric display, bounded embedding reconciliation/recovery UI and browser regressions. |
| Infrastructure | Compose/config changes, CI browser/PostgreSQL gates, non-root compiled web/API image, verification and restore tooling. |
| Other | Documentation consolidation, execution history, declining source-size baseline; frontend lockfile changes for nanoid and postcss. |

## 5. High-risk changes

- Architecture: multiple extracted services now own transaction and provider boundaries; review the
  whole call chain, not isolated helpers. The frontend shell still has roughly 8,010 lines.
- Authorization/workspace isolation: fresh role checks, workspace filters and lock ordering need
  resource-by-resource review. Existing denial tests do not prove a complete role matrix.
- Schema: migrations 0026_model_call_reservations, 0027_embedding_dimensions, 0028_ai_attempt_status,
  0029_retrieval_outcome, 0030_evaluation_reservations, 0031_graph_step_sequence and
  0032_execution_ownership. Later downgrades deliberately reject incompatible recorded history.
- API contracts: additional response-language/trace/retrieval fields, explicit evaluation outcomes,
  generic correlated 500 responses and embedding recover/reconcile endpoints.
- Provider behavior: durable pending estimates before external embedding I/O; PostgreSQL advisory
  session ownership, explicit uncertain results and no age-only reservation release. Session-pooling
  assumptions and ambiguous connection/commit failures need careful review. Model-call recovery is incomplete.
- Tests changed with behavior: migration-head expectations, reservation-expiry retention, evaluation
  nullable/renamed metrics and incompatible comparison results; pagination fixtures normalize ordering.
  These expectations require independent contract review to avoid circular validation.
- Browser tests now deliberately gate a refresh and inject a save 503; a document locator changed from
  group to combobox; recovery status locators are more specific. The 75-second timeout is unchanged.
  New profiler instrumentation also has the type-check failure recorded below.

## 6. Current verification evidence

No new full acceptance run was performed for this checkpoint. Saved logs were inspected.

| Evidence | Result | Scope/limit |
| --- | --- | --- |
| `.artifacts/20260908T004216702Z/checks.json` | 17/17 gates exit 0 | Historical worktree, predates later ownership/recovery changes |
| Same run `backend-tests.log` | 669 passed, 1 warning, 334.25s | Historical full PostgreSQL-enabled backend suite |
| Same run browser/build/lint records | Backend lint, frontend build, 27 browser journeys and compiled-image gate passed | Does not establish current full acceptance |
| `.artifacts/embedding-recovery-broader.log` | 103 passed, 1 warning, 120.89s | Later embedding/recovery/ownership backend boundary; Ruff passed in that command |
| `.artifacts/embedding-recovery-ui-build.log` | TypeScript/Vite build passed | Application build before profiler-only test edit |
| `.artifacts/embedding-recovery-ui-verified.log` | 4 passed, 17.4s | Recovery UI happy/failure/permission/lost-response paths |
| `.artifacts/embedding-recovery-ui-diagnostics.log` | 28 passed, 1 failed | Latest saved full mixed browser suite, ten workers |
| `.artifacts/loopback-worker-probe.log` | 20/20 navigations completed | Separate-browser diagnostic, not application acceptance |
| `.artifacts/navigation-editor-repeat.log` | 0 passed, 10 failed | Ten simultaneous copies of one heavy editor journey; 75-second timeouts |
| `.artifacts/navigation-cpu-profile.log` | 3 passed, 34.0s overall | Already-started three-worker profiling run; not a correction or full-suite replacement |
| Documentation/source-size/tooling checks from prior pass | Passed; 179 application files; 26 tooling tests | Before latest profiler edit; tooling tests simulate success and failure |
| Checkpoint standalone diagnostics type check | FAILED, TS2591 at fixture line 39: cannot find name process | Latest opt-in profiler uses process.env without Node types in this standalone check |

Failing command (frontend directory):
`npx.cmd tsc --ignoreConfig --noEmit --skipLibCheck --target ES2022 --module ESNext --moduleResolution Bundler --strict tests/e2e/agent-network-fixture.ts`

Runtime evidence includes synthetic multilingual import/knowledge/agent/review/evaluation/cost browser
journeys, restricted roles/workspaces, provider error injection, PostgreSQL concurrency/migrations,
child-process embedding ownership loss, HTTP privacy and earlier restored-application drills.
Automated provider tests use mocks/synthetic transports; none establishes real semantic AI quality.
A recorded FastAPI/Starlette warning concerns deprecated httpx TestClient integration.

Inspected trace evidence: the original mixed-suite navigation reports ~55.8 seconds in the CDP DNS
phase. Ten repeated editor journeys instead had DNS below 11ms and some 32–54-second save clicks.
The first slow click was already visible/enabled/stable; ~38 seconds elapsed during click dispatch,
before the scheduled-navigation wait. The new CPU profiles were captured but have NOT been analyzed.
The recovery screenshot was previously inspected. No current CPU root cause is established.

## 7. Known failures or uncertainty

- Full mixed browser acceptance remains 28/29, and ten heavy concurrent editor journeys time out.
- Latest profiler fixture fails the explicit standalone type check. It remains unchanged for review.
- No full backend/build/browser/compiled-image pass covers all current changes together.
- No complete permission/resource matrix, real-provider semantic benchmark, comprehensive factual
  entailment grading, global PII redaction/retention or hosted CI execution proof.
- Model-call ownership/recovery, whole-operation deadlines and ambiguous failure cases remain open.
- Redis is not an implemented worker queue; graph snapshots do not implement durable resume.
- Default Compose frontend is Vite development mode; production TLS/secrets/operations remain incomplete.
- Exact pre-goal dirty state and authorship of every current change are not reconstructable from HEAD alone.

## 8. Changes that may be unnecessary or over-broad

- 312 files before this report is too broad for one reviewable change. Multiple independent concerns
  accumulated across security, AI runtime, frontend, schema, infrastructure and documentation.
- Compiled deployment and restore tooling may deserve separate review/delivery from immediate critical-flow fixes.
- The volume of execution-history Markdown and repeated evidence summaries may create maintenance overhead.
- Source-size ratcheting constrains growth but does not prove architecture quality; extraction alone is insufficient.
- Frontend postcss/nanoid lockfile updates need explicit rationale reviewed independently of feature changes.
- Browser CDP/profiler instrumentation and ignored probes are investigation scaffolding; the profiler has
  no established corrective value yet. Review whether to retain it after diagnosis.
- No speculative DNS flag or timeout increase was shipped. No changes are reverted in this checkpoint.

## 9. Current git diff summary

Before this report, tracked `git diff --stat`: **74 files, 1,775 insertions, 1,961 deletions**.
Untracked files are NOT represented in that stat: **238 files, 18,232 text lines** before this report.
Including this report: **313 changed/untracked files**, all unstaged; tracked stat remains unchanged.
Ignored `.artifacts` include local logs, probes and snapshots; ordinary git diff also excludes them.
Git warned that the user-level ignore file was inaccessible, so global-ignore policy was not verified.
No commit, reset, stash, cleanup or staging operation was performed for this checkpoint.

## 10. Commit/base point

Current HEAD: `18a977fe4834d39545d71a1e271dd9913cf82a83`
Subject: `fix: execute active prompts and record provenance`.
The earlier full verification revision.txt records this same HEAD. This is the identifiable comparison
base for the current dirty worktree; it is NOT proven to be the exact clean state before the goal began.
Local reflog also contains clone point `d479329d9ffe5d2f66eb88f454954aae74ad11ff` and the subsequent HEAD
commit. The original request predates retained execution details, and existing uncommitted work was
preserved. Neither reflog entry proves the exact pre-goal file contents. Do not reset to either as an
assumed complete checkpoint.

Implementation is paused. Await user review; do not resume the improvement loop automatically.
