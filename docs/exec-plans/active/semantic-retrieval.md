# Semantic retrieval integration

## Goal
Provide compatible semantic document/query embeddings with attributable usage and verified
EN/JA/ZH retrieval quality, preserving workspace isolation and deterministic tests.
## Context
Embedding storage supports variable dimensions. Mock is the default; opt-in OpenAI indexing and
query embeddings now use the accounted provider with shared configuration and bounded batches.
Default retrieval uses lexical scoring. Initial inspection found missing vector compatibility checks.
See [RAG design](../../rag-design.md) and [token economy](../../token-economy-design.md).
## Requirements
Match provider, model and dimensions before comparing vectors. Bound and validate provider
responses. Record model attempts and usage. Authorize before transmitting protected text.
## Non-goals
Paid calls without authorization, invented semantic quality, or unaccounted embedding adapters.
## Acceptance Criteria
Compatible indexing/query configuration works; incompatible vectors cannot supply evidence;
invalid provider responses fail explicitly; PostgreSQL migration retains existing data;
mock transport tests cover failures; controlled multilingual semantic quality has evidence.
## Plan
1. Enforce vector compatibility in retrieval with focused regression tests.
2. Introduce dimension-flexible storage with PostgreSQL upgrade and recovery verification.
3. Integrate bounded provider transport and workspace-attributable accounting into indexing/search.
4. Verify the complete workflow and controlled semantic quality when paid calls are authorized.
## Verification
Focused retrieval tests, backend lint, PostgreSQL migration tests and full affected workflow tests.
Retain failed and successful commands under `.artifacts/20260907-vector-compatibility/`.
## Risks
Model names alone do not describe provider revision drift. Mixed indexes need explicit reindexing;
provider timeout may leave uncertain billable usage. Migration must not truncate historical vectors.
## Progress
2026-09-08 failed retrieval verification: full PostgreSQL-enabled suite passes 414 tests; final
focused run passes 13 after adding empty-search outcome coverage and failed graph trace-ID
assertions. All 12 browser tests pass on revision 0029. Lint, documentation, source-size and
whitespace checks pass. Historical outcomes remain unknown; pre-trace validation and persistent
database outages remain outside the failure-persistence guarantee. Details are in testing.md.
2026-09-08 failed retrieval diagnostics increment: add explicit outcome/error code fields with
historical outcomes marked unknown; preserve post-validation embedding failures at the direct
API transaction boundary and return a trace ID. Graph callers retain their own transaction
ownership. A workspace-permission-gated trace read exposes diagnostics. Extract query-vector
validation to keep retrieval orchestration below 300 lines. Verify failed provider/response/
stored-vector cases across request sessions, denied/foreign reads, graph behavior and migration
upgrade/downgrade preservation. Initial focused run passes 18 tests; migration fixture accessed
a detached ORM instance and is corrected. Import/line-length lint findings are also corrected.
2026-09-08 citation integrity verification: full PostgreSQL-enabled backend suite passes 411
tests; all 12 browser tests pass against the rebuilt mock API. No API HTTP 5xx records were found
during browser verification. Ruff, documentation, source-size and whitespace checks pass. One
existing dependency deprecation warning remains. Mixed canonical references now route to review;
real semantic quality, factual support and noncanonical invented references remain open.
2026-09-08 citation integrity increment: inspection found that one valid citation masked extra
invented canonical chunk references. Add a deterministic packed-citation check in the shared
validator used by guardrails/routing/publication, with unit and EN/JA/ZH workflow regressions.
The first unit run reproduces four invalid-reference acceptances. Initial multilingual fixtures
also exceeded reserved mock output and were corrected to isolate successful provider output
with mixed citations. Focused verification passes 36 tests; one PostgreSQL-only test is skipped
in that run and is included in the full PostgreSQL-enabled run. No factual-entailment claim.
2026-09-08 operator UI: added a focused Costs panel, typed API module and lifecycle hook without
growing the 8,067-line shell. Bounded pagination, pending protection, explicit errors, retained
confirmation drafts and owner/read-only controls are verified in Chromium with simulated
embedding responses and live surrounding auth/workspace/Costs requests. All 12 browser tests
pass; two focused tests also pass with request-failure assertions. Build and source-size checks
pass. Initial selector and StrictMode fixture failures are preserved. A full-run screenshot
showed an unexplained shell fetch-error toast; isolated diagnostic rerun had no failed requests.
This does not prove real provider billing recovery or resolve pending attempts. See testing.md.
2026-09-08 reconciliation API verification: full backend suite passes 399 tests; after adding
the budget-release regression, all 22 focused reconciliation tests pass. Backend lint,
documentation, source-size and whitespace checks pass. Rebuilt mock API is healthy and exposes
the protected routes. Evidence and exact scope are in testing.md. Next: owner-facing controls
and browser recovery/permission coverage; uncertain usage is now recoverable through the API,
but pending crash recovery and real semantic quality remain open.
2026-09-08 operator reconciliation increment: implement a bounded workspace-scoped unresolved
attempt list and owner-only confirmed-usage mutation. Separate request schemas, API permission
handling, transaction service and API/PostgreSQL tests. Require billing evidence reference,
retain admission-time pricing, commit audit plus usage atomically, reject pending/terminal
attempts and preserve failed output status. Verify concurrent stale readers, audit rollback,
invalid input and denied/foreign/archived operations. Operator UI and pending crash recovery
remain subsequent work; this increment does not establish full operator recovery or AI quality.
2026-09-08 graph attribution: graph-run identity now travels through the backend-created retrieval
tool closure to embedding admission. Admission checks workspace ownership, agent/per-run budgets
and current ledger/reservation usage. Retrieval node extraction links query attempts to their
graph step and records explicit failure/review routing. Initial checks caught an over-removed
shared import; restoration passes 43 affected tests. Foreign-ID and remaining-allowance tests
were added before full verification: 378 backend tests pass in 209.25 seconds and ten browser
tests pass in 31 seconds on the rebuilt mock-mode API. Final lint/docs/size/whitespace gates pass.
The graph runner shrank from 732 to 627 lines. Operator reconciliation and real semantic quality
remain open. Evidence: `.artifacts/20260908-graph-embeddings/`.
2026-09-08 runtime: wired indexing and retrieval to shared provider configuration; missing key,
price and invalid dimensions fail settings validation. Extracted knowledge contracts/indexing,
bringing the management service under 300 lines and removing its size exception. Configured
EN/JA/ZH API tests verify vector persistence, query ranking, authorization and attributable calls.
Failure tests verify explicit failed indexing with retained uncertain usage; batch tests cover
count/byte limits and rejection before any dispatch. Full backend: 369 passed in 193.42 seconds;
ten browser checks pass on the rebuilt mock-mode API; migrations 0027/0028 applied successfully.
Final lint, 17 tooling tests, documentation/size/whitespace gates pass. Evidence is retained under
`.artifacts/20260907-embedding-runtime/`. Real semantic benchmarking, per-graph embedding budgets
and attribution, and operator reconciliation remain open; the plan is not complete.
2026-09-07 accounting: revision 0028 adds pending/uncertain AIRun states; an independent PostgreSQL
ledger transaction admits embedding usage against monthly budgets before dispatch. The accounted
provider reconciles success and retains unknown usage without retrying or releasing allowance.
Initial verification reproduced a caller foreign-key lock conflict; NO KEY UPDATE fixed it.
Twenty affected PostgreSQL/budget/migration tests pass. Final full backend verification passes
356 tests in 198.79 seconds; lint and repository gates pass. Runtime factory/configuration,
batching, operator reconciliation, graph-run linkage
and real semantic-quality evidence remain open.
2026-09-07 API boundary: added bounded OpenAI embedding requests and strict response validation.
Thirty synthetic tests pass for input limits, ordered vectors, model/usage validation, malformed
responses, sanitized errors, response-size limits and redirect rejection. Backend lint passes.
This API client is not wired into indexing or retrieval: durable admission/accounting must own
the call before runtime configuration can enable it. No paid API request was made.
2026-09-07 storage: revision 0027 widens the vector column without rewriting vector values.
33 affected tests pass, including real PostgreSQL data preservation, safe downgrade/re-upgrade,
1,536-dimensional ORM storage and refusal of an unsafe downgrade with revision/data unchanged.
Initial lint found import formatting and a long line; both were corrected before final validation.
Provider integration and real semantic-quality evidence remain open.
2026-09-07: implemented provider/model filtering and explicit vector validation. Initial tests
reproduced six failures; the first 31 affected tests passed after repair. Added stored-vector
corruption coverage before query dispatch. Full backend verification passes: 318 tests including
opt-in PostgreSQL checks, in 154.51 seconds. Backend lint, documentation, source-size and whitespace
checks pass. One existing Starlette/httpx deprecation warning remains. Provider integration,
dimension-flexible storage and real semantic quality evidence are still open.
## Decisions
Lexical retrieval does not require embedding-model compatibility because it does not score vectors.
Vector/hybrid candidates must match the configured provider and model before query dispatch.
## Findings
Full verification also exposed a dataset pagination test's dependence on host wall-clock order.
Its chronological fixture now has explicit timestamps without weakening its order assertions.
A separate forced-tie regression failed before adding dataset ID as the secondary sort key.
An additional evaluation pagination failure exposed the same clock assumption. All four affected
pagination fixtures now use explicit timestamps. Failed runs are retained under
`.artifacts/20260907-embedding-attempts/`; the final full run passes. This does not establish
snapshot pagination during concurrent writes or deterministic ties for every resource list.
The existing `record_ai_run` helper commits the caller's session. Indexing already has pending
document/version writes when embedding begins, so reusing it would commit partial document state.
AIRun initially had only succeeded/failed states. Revision 0028 now adds pending/uncertain states
for embedding dispatch with separate transactions. Caller foreign keys hold key-share locks on
workspace rows; admission uses NO KEY UPDATE, preserving spending serialization while allowing
those references. Unknown usage estimates are not automatically released; monthly admission
counts attempts created in that calendar month. An owner-only uncertain-usage reconciliation API
now exists; operator UI and safe recovery of pending attempts remain open.
The current cosine helper returns zero for dimension mismatches, allowing invalid data to look
like ordinary low relevance. Explicit validation is required for vector-scored candidates.
## Final Result
Open. Compatibility alone does not complete semantic retrieval or prove real AI quality.
