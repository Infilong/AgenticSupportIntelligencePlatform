# Data processing administration

## Goal
Implement the active goal attachment `14827e8b-063e-4e67-83c1-f50555e2d50d/pasted-text-1.txt`:
user data -> persisted input -> AI/tools -> results, metadata and intermediate artifacts,
with permission-scoped administrator inspection/intervention and knowledge management.
The approved product areas are Records, Knowledge and Settings, plus an embedded Ask assistant.

## Context
Baseline HEAD: `18a977fe4834d39545d71a1e271dd9913cf82a83`. The checkout already contains extensive
uncommitted work. `.artifacts/data-admin-baseline/tracked.patch` and `status.txt` capture tracked
changes/status before this goal's edits; untracked files are not backed up by that patch.
Do not reset or discard existing work. The previous conversation-centered proposal is superseded.
Existing SupportTask already persists original text input and TaskExecution links multiple runs;
reuse that relationship rather than inventing a second competing input identity. Extend it for
origin/structured data explicitly. Legacy run-only history needs a deliberate migration/view policy.

## Requirements
- Records: bounded searchable list, received time/status/result summary; Overview, Processing,
  Artifacts views. Show results/actions first and evidence in context. No duplicate Activity area.
- Persist original input, origin and ownership; separate attempts, steps, artifacts, results,
  interventions and knowledge versions with explicit workspace-scoped links.
- Worker processing survives browser closure. Clarification, approval, failure and stop are distinct.
  Meaningless input requests clarification, not admin review; preserve legitimate short/CJK input.
- Real LangChain/LangGraph execution, backend-owned authorization/accounting/approval, bounded
  steps/time/cost, idempotent actions, recovery and cancellation at safe boundaries.
- Knowledge originals and TXT, DOC, DOCX, PDF extraction; durable uploaded/extracting/chunking/
  embedding/ready stages, errors/retry, extraction preview, versioned references. DOC conversion
  is isolated; scanned PDFs get OCR or explicit requires-OCR outcomes. No false ready states.
- Real embeddings and database-side vector ranking, permission filters before model context,
  compatible dimensions/models, long policy/exception/version evaluation.
- Embedded assistant reads actual permitted records, cites evidence, compares attempts and proposes
  useful actions with exact-input confirmation. Ordinary controls remain available.
- Modern readable responsive UI, keyboard navigation, long content/error states, technical details
  on demand. Intermediate evidence excludes private chain-of-thought and follows retention policy.
- Verify real-provider quality, permissions/isolation, worker restart, outage/duplicates, extraction
  recovery, backup/restore, deployment/health and browser journeys before completion.

## Non-goals
No external channel integration, arbitrary shell/SQL agent tools, workflow canvas or broad legacy
cleanup unrelated to this data flow. No mock-only completion or unsupported production claims.

## Acceptance Criteria
Each requirement above needs an evidence row before completion. Initial gates: records grouped by
input rather than attempts; immutable original retained on retry; no cross-workspace disclosure;
correct clarification/approval states; each format ingestion demonstrated; real SQL vector search
and long-document answers; assistant reads and confirmed action; stop/restart/duplicate proofs;
visual review at 360/768/1280/1440 widths and 200% zoom; verified restore and built deployment.
Use the prior proposed long policy corpus/evaluation requirements as acceptance detail: 30–50-page
synthetic handbook with coherent exceptions/versions and EN/JA/ZH evaluation, not tiny demo snippets.
Freeze evaluation thresholds and latency budgets before tuning and report per-language failures.

## Plan
1. Record domain: scoped list/detail APIs over persisted inputs and linked attempts; extend intake
   metadata and artifact/result contracts; safe migration for legacy records.
2. Workflow: explicit clarification/no-answer/approval routes, durable lifecycle and recovery tests.
3. Knowledge/RAG: format extraction worker, originals/versions, real SQL retrieval and evaluation.
4. UI: Records list/detail, Processing/Artifacts views, Knowledge and Settings; consistent design.
5. Embedded assistant: scoped evidence tools then explicitly confirmed effects.
6. Full acceptance: real provider, Chrome visual/journeys, reliability/security, restore/deployment.

## Verification
Use focused backend pytest, Ruff, docs and source-size checks per slice; PostgreSQL tests for SQL,
transactions and migrations; compiled frontend browser tests plus actual Chrome visual review.
Preserve failure evidence. Do not infer provider quality from mocks or database behavior from SQLite.

## Risks
Real-provider credentials/spend are not yet revalidated. New extraction dependencies may require
explicit dependency approval under codingRules.md; prepare concrete choices first. Do not expose
secrets while checking readiness. Retain useful prior data and test migration on an isolated copy.

## Decisions
2026-09-08 ingestion implementation design: use a workspace-scoped upload job, preserving bounded
original bytes and SHA-256 in PostgreSQL so the local backup includes originals atomically. Limit
originals to 20 MiB; keep bytes out of list/detail responses and serve originals only through a
permission-checked download endpoint. Store extraction output and page/section warnings separately.
Worker claims jobs durably with bounded leases; stages uploaded/extracting/chunking/embedding/ready
and failed/requires_ocr are explicit. Index into an exact linked DocumentVersion; retries retain
the original and avoid duplicate versions. Existing historical text versions remain available.
Proposed parser dependencies: pypdf for text PDF with page markers; python-docx for ordered DOCX
paragraphs/tables; headless LibreOffice confined to the conversion container for legacy DOC.
Do not install desktop software. Conversion runs without network, with memory/time/output limits,
temporary per-job directories and disabled macros. Scanned/empty PDF returns requires_ocr;
OCR itself is not required for this first format path. No parser may silently mark empty output ready.
Dependency additions require approval under codingRules.md; approval is pending. Durable job/model/
API work can proceed independently. Acceptance includes corrupt/encrypted/oversized/scanned files,
EN/JA/ZH content, retained originals, permission denial, worker restart and retry after failure.

2026-09-08: active user goal authorizes implementation of the record-centered direction.
One focused implementation owner. First slice adds a read API with schema/service/route/tests
separated, no schema migration or UI changes. Later slices supply broader intake and artifacts.

## Progress
2026-09-08: read complete goal, coding rules and current persistence boundary; baseline captured.
First slice implemented: `GET /workspaces/{workspace_id}/records` and `/{record_id}` return
one list entry per persisted input, latest attempt and attempt count. Search escapes SQL wildcards;
pagination is bounded. Schema, queries and routes have separate ownership. No migration/deployment.
Verified: `python -m pytest tests/test_records_api.py tests/test_task_api.py -q` (backend cwd):
5 passed, one existing Starlette/httpx deprecation warning; focused Ruff passed. This is SQLite
API evidence, not full PostgreSQL acceptance. A subsequent read-only PostgreSQL smoke of the same
service against QA Real User EN-JA-ZH returned 10 records, a bounded page of 2, and matching detail
responses. No production data writes. Docs and source-size checks pass (221 source files).
Still need isolated PostgreSQL regression tests, explicit source/structured payload intake,
complete attempt/artifact views, and legacy run-only handling. Next: finish the record domain
contract and clarification lifecycle before connecting the replacement UI.

## Findings
2026-09-08 upload storage groundwork: added KnowledgeUpload and additive migration 0040 with
workspace/actor ownership, idempotency identity, bounded original bytes/hash, processing state,
attempt/lease fields, deferred extracted text/metadata, errors and linked document version.
Ordinary ORM reads defer originals and extracted content; explicit extraction/download services
will own loading. Database constraints reject empty/over-20-MiB originals and ready without a
version/text. Populated downgrade refuses data loss. One isolated PostgreSQL migration test passed:
0039 -> 0040 -> empty downgrade -> 0040, retained workspace and binary EN/JA/CJK bytes, deferred
loading, invalid-state/empty-data rejection, and populated downgrade refusal without data loss.
No main database deployment or ingestion API/worker yet. No parser dependencies installed.
Next slice: bounded original-byte admission/download and status APIs with server permissions,
then worker/extraction and Knowledge UI. Ingestion is not yet a usable feature.

2026-09-08 current-schema restore: a fresh 0039 logical backup restored successfully into a
generated isolated database; all 41 table count/content fingerprints matched. Initial drill
fc3a296591e24c729e58e515a0949bc6 passed in 39.359 seconds. Extended restored-app probe with native
Records JSON admission, immutable originals after processing, duplicate replay, saved artifacts,
unauthenticated denial and cross-workspace denial for EN/JA/ZH. The expanded drill also passed:
`.artifacts/database-restore-bbe17534fa2d46bb96ca71899d424325/report.json`.
Existing login/read/task/stop checks remain intact. Source manifests stayed unchanged and the
generated restore target was removed. Two harness tests passed including injected failure/cleanup
cases; scoped Ruff passed. This verifies current local database recovery with mock providers,
not off-host disaster recovery, a production cutover or the older pre-0039 archive's restoration.
Parser dependencies remain awaiting explicit user approval; no installation was performed.

2026-09-08 PostgreSQL retrieval coverage expanded: seven tests now pass. Deliberately incompatible
vectors in another workspace, wrong language/model, failed document and obsolete version are
excluded before validation/provider dispatch; the eligible current document remains retrievable.
These are real PostgreSQL tests with disposable schemas, not compiled-SQL-only assertions.

2026-09-08 database vector ranking: confirmed prior retrieval loaded every stored candidate and
computed cosine in Python. Extracted shared permission/version/model-scoped candidate SQL into
retrieval_candidates.py. PostgreSQL now ranks with pgvector cosine and LIMIT; vector-only fetches
top-k and hybrid reranks max(100, 10 * top-k) vector neighbors. Stored dimension/zero checks run
in SQL before query embedding; empty eligible selection avoids provider dispatch. SQLite retains
the deterministic fallback. Two isolated PostgreSQL tests passed for actual ordering/operator,
selected-document restriction, empty selection and incompatible dimensions. Ruff and source sizes
passed (239 files). No schema migration, provider configuration or main runtime deployment changed.
Hybrid recall, cross-workspace/latest-version PostgreSQL expansion, large-corpus latency and real
provider evaluation remain to verify; lexical candidate loading is still unbounded. Do not call
the entire RAG milestone complete from this database boundary proof.

2026-09-08 native intake: replaced Records' Work submission link with an inline New record form.
RecordIntake renders text/JSON input and optional reference/language; useRecordIntake owns bounded
agent pagination, validation, submission state and stable idempotency keys; RecordsApi owns POST.
Existing backend admission and permission checks remain authoritative. Successful creation opens
the persisted record; original whitespace is retained for text and source is admin.
Build passed; two responsive browser tests passed including invalid JSON (no submission), a 503
response, retry with the same key, then detail/clarification/review. Expected 503 console output is
excluded explicitly; other console errors still fail. Source-size check passed (238 files).
Deployed only frontend and submitted structured JSON in actual Chrome with reference
QA-NATIVE-INTAKE. The live worker reached review; detail showed Source: admin, original typed
fields and source reference. Chrome console errors empty; desktop screenshot inspected.
Remaining: JSON list titles still look technical, original data sits below long review content,
and legacy run-only history remains separate. Real-provider and full knowledge gates remain open.

2026-09-08 live integration: backed up the main verification database to
`.artifacts/data-admin-baseline/before-0039.dump` before deployment (restore not yet verified).
Built API/worker/frontend and deployed `asi-verification`; API healthy, worker started, schema 0039.
In actual Chrome, a fresh `w` requested clarification with one saved step and no model calls.
Submitting the refund-policy clarification created a second attempt and retained original `w`.
Approved category, rejected the duplicate mock note with a reason, and published a human answer;
the record became completed. Historical original attempt and its clarification remained accessible.
Found that the reply was absent from the record overview. TaskAttempts now loads selected attempt
metadata when not supplied, displays clarification reply and parent link, and reports lookup errors.
Build and two fixture browser tests at 360/1440 passed, including visible reply and zero console errors.
Rebuilt/restarted only frontend; actual Chrome confirmed persisted result, reply, original and history.
Chrome error logs were empty. Source-size check passed (236 files). This proves this narrow mock
workflow only: real-provider RAG, long-document ingestion, production deployment and restore remain open.
Remaining UX findings: browser reload selects first workspace; intake still uses transitional Work
and reports unknown origin; historical clarification received is labeled completed; source labels
still expose chunk UUIDs. Native Records intake and clearer history/source presentation are next.

2026-09-08 inline intervention: added review lookup scoped to record, attempt and reviews:read.
Records reuses the existing approval/action form inline and embeds attempt history/retry controls.
Selecting history changes the viewed run and its artifacts while preserving original record identity;
historical attempts are labeled. Removed the execution-controls link to Work from record detail.
Build passed, scoped review API test passed, and two 360/1440 fixture-based browser tests passed
including edit/publish inline. Live API deployment, browser integration and legacy-input migration
remain open; this is not a full feature acceptance claim.
Preview logs exposed sibling React keys colliding between actions and review forms; keys now have
distinct prefixes. Added a console-error assertion and reran both browser cases successfully.

2026-09-08 Records UI slice: Records is now the default source route, with Records/Knowledge/
Settings main navigation. New records modules separate API, polling, list/detail, artifact rendering
and actions. Overview shows original typed input/result, Processing shows steps/model accounting,
Artifacts reads the scoped saved-output API. Clarification and stop controls are inline; stale
workspace fetches are discarded. Small screens use list/detail navigation and selection focuses
the detail heading. Agent configuration is reachable through Settings. Transitional Work controls
and run-only history remain linked pending migration; they are not the finished three-area UX.
`npm run build` passed. Two Playwright interaction tests at 360/1440 passed against mocked APIs
on a local Vite preview, including focus, tabs, clarification and overflow. This is not live Chrome
or backend integration proof. No Docker deployment/main DB migration. Next: integrate approval/
attempt history into Records, migrate legacy run-only input identity, deploy safely and inspect
actual Chrome layout/flows before calling this UI milestone complete.

2026-09-08 artifacts slice: added permission-scoped, paginated saved step artifacts keyed by
record and attempt. Projections select explicit output fields, preserve source-version metadata,
omit arbitrary/private state and apply existing response redaction. Invalid saved JSON is reported
instead of silently disappearing. Source/schema/route/test ownership is separate; no new storage.
Focused two-test API suite passed for actual saved data, corruption, pagination and foreign-record
denial. UI rendering, full artifact lifecycle/retention and assistant integration remain pending.

2026-09-08 clarification slice: a conservative preflight graph branch handles standalone Latin
single letters and punctuation-only input. It produces awaiting_clarification without model calls,
policy-answer guardrails or an admin review. Requested EN/JA/ZH is honored; otherwise English is
explicitly marked default, not detected. Initial tests exposed punctuation failing language detection;
the branch now runs before detection. Short words/CJK and contextual replies are not length-rejected.
POST /records/{id}/clarifications binds a reply to a waiting attempt, preserves original input, creates
a linked attempt, marks the question received, and audits the transition. Migration 0039 stores the
reply separately from corrected instructions and refuses lossy downgrade. Read/history APIs expose it.
31 focused tests passed; 10 PostgreSQL worker tests passed before reply integration; the subsequent
8-test PostgreSQL migration/concurrency/attempt suite passed. Another 16 authorization, graph-order
and budget regression tests passed. Focused Ruff, docs and source-size (224 files) passed. This is not yet
semantic ambiguity detection, a no-knowledge outcome, or a browser-verified clarification interface.
No deployment/main DB migration. Next: record attempts/artifacts views and the replacement UI,
plus semantic clarification and missing-knowledge routing within the real-provider milestone.

2026-09-08 intake slice: migration 0038 adds nullable original-input storage to SupportTask.
RecordInput owns bounded text/JSON validation and caller-declared provenance; POST /records
passes authenticated identity to atomic admission, binds original data into the idempotency hash,
and retains it across retries. Record detail exposes original data; legacy source is unknown.
23 focused SQLite tests pass (intake, record reads, task API/admission/attempts). Five PostgreSQL
tests pass (new migration, admission concurrency, attempts). Ruff passed. The first PostgreSQL
run found the historical 0034 fixture using current ORM against an old schema (UndefinedColumn).
Preserved its migration round-trip/loss-refusal assertions with historical SQL fixtures, then
upgraded to head before current-code concurrency checks; the rerun passed. Tests were not relaxed.
No main database migration or deployment yet; current containers remain on the previous build.
Next: clarification state and follow-up data, then artifact/attempt API and the Records interface.

SupportTask/TaskExecution already provides stable input-to-attempt identity. Existing UI lists
GraphRun instead, making retries look like separate inputs. Existing guardrails still escalate no-source.

## Final Result
Not complete. All milestones and full acceptance remain open.
