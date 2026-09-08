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
