# M2 — real document retrieval, simulated generation transport

Status: active after the M1 foundation slices. Full M1–M6 authority remains in effect.
Unattended checkpoint deadline remains 2026-09-08 17:34 UTC; this is not a new time allowance.

## Execution brief

Deliver uploaded policy → stored original → bounded worker chunks → real local embeddings →
PostgreSQL vector/lexical retrieval → visible source passages. Development generation is a
separate mock/Codex-assisted contract and cannot manufacture retrieval evidence.

Slices: (1) pinned CPU embedding dependency and observable model preparation; (2) document
version/chunk persistence, upload/indexing worker and permissions; (3) knowledge UI and real
retrieval inspection; (4) expanded frozen corpus/cases and retrieval measurement; (5) grounded
development draft handoff. Commit/push verified slices, inspect CI and continue autonomously.

Use multilingual-e5-small with pinned model revision, 384 dimensions, normalized vectors and
the model's required query/passage prefixes. Keep inference local, disable remote code loading,
and prepare weights explicitly. No API key, paid calls, GPU, Redis or external vector service.
Record actual embedding duration/model/input-token estimate, with zero API charge clearly
distinguished from a provider-reported bill. Tests may inject deterministic embedding providers;
runtime acceptance must also exercise the actual CPU model and PostgreSQL vector operations.

## Boundaries and acceptance

- Preserve uploaded originals/checksums and exact version/section offsets; activate replacements
  only after successful indexing. Exclude withdrawn/superseded/foreign data before retrieval.
- Use LangChain splitting, model-token-aware limits and bounded batches. Check cancellation,
  actor access and current lease between batches; stage chunks and publish under the job fence.
- Freeze at least 30 cases (10 per language) and 30–50 page-equivalent synthetic company policy
  before retrieval tuning. Expected sources/facts are evaluator inputs, never app runtime inputs.
- Preselected recall@5 target: at least 90% overall and 80% in each language on answerable cases.
  Forbidden-version/workspace leakage must be zero. Unsupported questions must not become a
  supported answer merely because vector search always has nearest neighbours.
- Record warm single-user query latency; initial target p95 <= 3 seconds on this CPU profile.
  Report a miss honestly; do not weaken thresholds after measurement.
- Browser acceptance: upload, progress/error, document list/detail, ask/test, exact cited passage,
  viewer denial for management, and preservation of the previous active version on failure.

Risks: model download/runtime compatibility; resource bounds; active-version publication races;
multilingual lexical segmentation; plausible mock answers hiding weak retrieval. Retain failures.
Sources: [model card](https://huggingface.co/intfloat/multilingual-e5-small),
[CPU packaging](https://docs.astral.sh/uv/guides/integration/pytorch/).

## Progress

- M1 worker pushed `5749308`, CI `34240525106` passed.
- Pinned model revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`; real Windows CPU
  inference produced EN/JA/ZH normalized vectors. Cold preparation included download/load
  (196 seconds); subsequent query took 47 ms. This is a smoke test, not retrieval scoring.
- Dependency compatibility: unit 6/6 and PostgreSQL 23/23 passed. One upstream AnyIO
  deprecation warning remains; httpx warning disappeared with the resolved httpx2 dependency.
- Added explicit input/batch bounds and disabled remote model code/implicit runtime downloads.
  Docker preparation and final verification are in progress before the embedding slice push.
- Final optimized image became healthy. Real inference inside the application model volume
  passed: preparation 28.8 seconds and warm query 15.24 ms, pgvector-ready app/worker healthy.
  Source-linked evidence `.artifacts/m0/prepare-model-20260908T150224785217Z`.
  Offline Windows cache loading also passed (`.artifacts/m2-model-offline.log`). No API calls.
- Independent ingestion design review selected bounded in-memory chunks followed by atomic
  insertion/activation, avoiding a partial staging subsystem. Use desired-version fencing,
  admin rechecks, composite ownership constraints and workspace→document→job lock order.
- Ingestion implemented: retained originals, bounded UTF-8 TXT/Markdown uploads, queued versions,
  real CPU embedding ledger and atomic vector/active-version publication. PDF/DOC remain pending.
  Eleven unit tests and 30 PostgreSQL tests pass, including withdrawal/replacement/demotion
  during embedding. Evidence: `.artifacts/m0/backend-20260908T153150040989Z` and
  `.artifacts/m0/integration-20260908T153232881757Z` (before documentation/contract updates).
- Actual API upload/worker smoke passed at `.artifacts/m0/ingestion-20260908T152911661659Z`:
  original 2,196 bytes preserved, two 384-dimensional pgvector rows, 483 embedding tokens,
  337.71 ms batch duration and zero API charge. This preceded bounded splitter refinement;
  final runtime recheck follows. It is not full-corpus retrieval evidence.
- Review found no concrete P0/P1 publication bug. Fixed worker health timeout by lazy-loading
  indexing imports; fixed demotion test transaction ownership without changing assertions.
  Split within headings and 8,000-character blocks, rechecking permission/cancellation between
  blocks; retain exact source offsets. Reject opaque ASCII tokens over 4,096 characters.
  Quota-race and publication-rollback fault-injection coverage remain to broaden in M2.
- Final bounded-splitter CPU ingestion passed:
  `.artifacts/m0/ingestion-20260908T153529065817Z`. Frontend generated contract/build,
  preparation 14/14, Ruff and documentation checks passed. Full retrieval evaluation remains next.
- Ingestion pushed `59fc6c9`; CI `34245863644` passed. Retrieval API now performs exact
  PostgreSQL cosine ranking with a lexical-overlap boost (not BM25), returning bounded exact
  passages and recording query embedding/retrieval metadata. Permission is checked before
  embedding and again under the workspace lock before reading source candidates.
- PostgreSQL integration 35/35 passed at `.artifacts/m0/integration-20260908T154451968045Z`,
  including best-scoring foreign chunks, replacement/withdrawal and mid-query revocation.
  Initial lexical comparator failure was fixed using PostgreSQL ARRAY rather than generic ARRAY.
- Real query smoke returned the 14-day policy and verified all five passage offsets against
  source previews. Trace `0fd9cc46-89fc-4d14-bf61-7eb4829a6a01`: 2,647.03 ms cold total,
  13 query embedding tokens. Not a corpus-quality or p95 result. Initial probe invocation used
  the wrong cwd; corrected to backend. Preserve `.artifacts/m2-retrieval-smoke.log` failure.
- Independent review: no P0/P1 filtering bug. Matched ORM unique constraint to migration;
  added adversarial foreign-chunk test. Abandoned synchronous retrieval/model-call records
  still need uncertain-state reconciliation in observability work; never call them completed.
- Retrieval pushed `f04b86f`; CI `34247160191` passed. Knowledge UI implements document lists,
  progress, original previews/downloads, versions, replacement/withdrawal/restore and real search.
  New browser journeys 2/2 passed with the real model (`.artifacts/m2/knowledge-ui-first`),
  existing journeys 5/5 passed (`.artifacts/m2/app-regression`), component tests 2/2 and build passed.
  Chrome desktop inspection showed the real refund passage; console errors/warnings empty.
  Narrow-layout evidence is from the application browser suite; the old Chrome viewport handle
  could not capture after tab recovery and was reset. Do not represent that as Chrome mobile proof.
- UI review fixes: citation links retain version/offset instead of following a newly active
  replacement; withdrawal suppresses contradictory search-availability banners; denied/not-found
  reloads clear protected document details. Successful uploads reset the native picker and search
  results retain their submitted query label. Final build and repaired browser journeys 2/2 passed
  at `.artifacts/m2/knowledge-ui-repaired`, including exact-version/offset navigation.
- Knowledge UI pushed `c9053a8`; CI `34248740061` passed. Expanded corpus: 81,502 bytes,
  10,129 English-style words and 3,997 CJK characters, 38.2 equivalents under the fixed
  300-word/900-CJK-character convention. Two long English manuals plus selected JA/ZH policies;
  not every long chapter has a translation. Thirty cases include 26 evidence-bearing cases.
- Pre-measurement review strengthened section discovery with factual-span coverage, explicit
  case-success/group-recall denominators, top-five enforcement, timing protocol and targeted
  leakage probes. Initial freeze snapshots are retained; no measurement preceded corrections.
  Runner checks actual API/worker code hashes and image IDs against the host backend before
  attributing results. Synthetic provisioning creates new workspaces without changing old roles.
- First frozen measurement failed: EN 8/8, JA 6/9, ZH 6/9 evidence cases; section groups
  20/27. Warm p95 0.156 seconds; no forbidden-version leaks and foreign access returned 404.
  Preserve `.artifacts/m2/retrieval-eval-20260908T163239Z/report.json` as the failed baseline.
- Repair brief (normal scoped investigation): inspect raw semantic candidates before changing
  ranking. Japanese trial-conflict sources occur at semantic ranks 15 and 17, below unrelated
  same-language passages. Equal-weight overlap fusion further favors same-script results.
  Experiment with a pinned local multilingual cross-encoder over bounded, authorized semantic
  candidates; measure the same frozen cases before integrating. No fixture edits, translations
  derived from expected answers, paid APIs or readiness claims. Keep the experiment separate
  from app acceptance; integrate only with permission rechecks, ledger and regression coverage.
- Local reranker experiment: 40 candidates recovered all 26 evidence cases/27 section groups
  but p95 was 4.43 seconds; 20 candidates retained the same coverage at 2.48 seconds.
  Evidence `.artifacts/m2/rerank40-results.json`, `rerank20-results.json`, `rerank20-summary.json`.
  These are diagnostic measurements, not app acceptance. Selected the bounded 20-candidate
  configuration, pinned model revision `1427fd652930e4ba29e8149678df786c240d8825`.
- Implemented snapshot → local inference → permission/current-version revalidation, separate
  reranking ledger, explicit source-change result, finite/count checks and internal-failure 503.
  Independent read-only review found no P0/P1; internal-error-as-422 finding was fixed. Token
  counts are locally computed, not provider billing. Frozen corpus and thresholds remain intact.
- First integrated API measurement recovered 26/26 cases and 27/27 groups, p95 2.5 seconds,
  zero leaks. `.artifacts/m2/retrieval-eval-20260908T165315Z` is NOT a final pass: concurrent
  test-source edits invalidated its source fingerprint. Repeat on a stable snapshot.
- First security suite had 41 passing/one failed revocation scenario; isolated rerun of all
  three change scenarios passed with an explicit indexed-source precondition. Root cause of
  that intermittent failure is not established. Preserve both reports; full-suite recheck pending.
- Full-suite recheck executed 43/43 tests successfully, but documentation edits during the run
  invalidated harness source-stability verification. Final checks must run after all edits stop;
  do not confuse test success with an overall evidence-wrapper pass.
- Final stable checks passed: PostgreSQL 43/43 at
  `.artifacts/m0/integration-20260908T165923103696Z`, backend 16/16 at
  `.artifacts/m0/backend-20260908T170045368182Z`, harness 19/19 at
  `.artifacts/m0/prep-20260908T170122375591Z`; browser journeys 2/2 at
  `.artifacts/m2/reranked-knowledge-ui`. Build/component tests passed; desktop/mobile artifacts
  were visually inspected. Chrome tab listing works, but interactive screenshot capture timed
  out twice; new visual proof comes from the application browser suite, not a claimed Chrome demo.
- Final actual API quality gate PASSED at `.artifacts/m2/retrieval-eval-20260908T170142Z`:
  EN 8/8, JA 9/9, ZH 9/9 cases; 27/27 required groups; warm p95 2.5 seconds; zero forbidden
  leaks; foreign request 404; unchanged source/runtime fingerprints. Generation and workflow
  outcomes remain NOT_VERIFIED. This corpus is a regression/acceptance set used during tuning,
  not an unseen generalization benchmark. No paid model calls were made.
- Retrieval pushed `01ee83f`; CI `34254935876` passed. Actual database ledger inspection
  (`.artifacts/m2/rerank-runtime-ledger.txt`) found 14 passage embedding batches, 33 query
  embeddings and 33 reranking calls, all local/succeeded with recorded tokens/durations and
  zero external charge. Explicit two-model preparation passed at
  `.artifacts/m0/prepare-model-20260908T170804920142Z`.
- Changed the ambiguous "Simulated AI" badge to "Simulated responses". Initial browser
  screenshots exposed an outdated frontend container; rebuilt it and added a visible-mode
  assertion to the knowledge journey. Final build and 2/2 desktop/mobile journeys passed at
  `.artifacts/m2/provider-label-rebuilt-ui`; the new mobile screenshot was visually inspected.

## Next execution brief — persisted cited development draft

Classification: deep; one implementation owner, bounded read-only security review.
User outcome: enter an original EN/JA/ZH customer message, inspect actual retrieval, and obtain
an explicitly attributed development draft with exact source links. Advances RAG/LANG/TRACE;
does not complete semantic generation quality, ordinary human review or release gates.

Use small message/run/handoff modules and the supported LangGraph PostgreSQL checkpointer.
Graph: validate → retrieve → pack bounded context → development-generation interrupt →
validate citations → persist draft. Keep jobs as scheduling, checkpoints as continuation,
domain records as user-visible history. Do not create a competing temporary workflow engine.

- Save immutable original text/requested language and message/run/job atomically. Operator/Admin
  may submit; Viewer reads. Apply workspace composite references and the existing lock order.
- Preserve prompt/config version, run/attempt identity, retrieval trace and context hash. A
  handoff exports only authorized original input and bounded source snapshots, never test answers.
- Pause as waiting for a development response, distinct from administrator review. The worker
  must be released. Resume uses a server-derived graph thread and authenticated domain endpoint;
  never accept arbitrary graph state from a client or unauthenticated file drop.
- Bind submissions to handoff/context/revision. Same submission is idempotent; conflicting or
  concurrent submissions fail. Recheck membership, cancellation and source validity before resume
  and publication. Preserve changed evidence as history and require fresh retrieval for publication.
- Validate citation ownership/version/checksum/exact quotes and offsets. This proves provenance,
  not semantic support: keep an explicit support-review status and the result as a draft.
- Attribute `codex_assisted_development`, contributor and handoff elapsed time. Do not invent an
  OpenAI API model, billed tokens or inference latency. External generation remains NOT_VERIFIED.

Verification: real API/UI/worker/retrieval/handoff/resume with one EN/JA/ZH example; restart while
waiting; duplicate/concurrent response, foreign denial, withdrawn/replaced source and revocation
tests. Read root/backend/frontend guides before edits, inspect current supported LangGraph APIs,
and review replay semantics before introducing schema or checkpoint effects. The same graph
will be extended in M3 for broader review/cancellation/retry behavior.

Independent read-only design review confirmed these boundaries. This is a plan, not implemented
message/graph behavior. Do not start a partial substitute if the existing unattended cutoff leaves
insufficient time to implement and verify the connected slice; preserve this exact resume point.

### Checkpoint prerequisite slice

Within the remaining unattended window, install/lock the supported LangGraph and PostgreSQL
checkpointer and verify its real database interrupt/resume and failed-node recovery contracts.
This is dependency compatibility evidence in isolated test schemas, not the application graph,
message API, human-review flow or workspace authorization. Preserve the existing retrieval
runtime, verify the resolved dependency set, and checkpoint before the original 17:34 UTC limit.

Result: locked LangGraph 1.2.11, checkpoint-postgres 3.1.2 (checkpoint 4.2.0); existing
LangChain/model packages remain unchanged. The resolver changed websockets 17.1 → 16.1.1.
Tests use real PostgreSQL in the fixture's isolated schema and fresh connections/graph instances.
They verify retained EN/JA/ZH input, interrupt/resume, persisted completion and failed-node
recovery. They do not prove an application workflow, process-kill recovery or authorization.

Initial failures came from SQLAlchemy URL query encoding ('+' spaces) passed directly to libpq;
fixed by supplying explicit connection options, retaining the schema. Preserve
`.artifacts/m0/integration-20260908T172152370097Z`. Focused 2/2 then full 45/45 passed;
final evidence `.artifacts/m0/integration-20260908T172545791661Z`. Unit 16/16, Ruff and rebuilt
four-service health passed. Runtime package versions were inspected. Real retrieval/source-span
smoke passed after rebuilding: trace `7503fc4e-a562-4bcd-9b57-2b8dbbb26d80`, 5,814.04 ms cold;
not a new warm latency or full-corpus quality measurement. No application checkpoint tables or
message workflow were introduced; next connected slice remains defined above.
