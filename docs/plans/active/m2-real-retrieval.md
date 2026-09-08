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
