# Milestone 5: Retrieval And Citations

## Goal
Add the first retrieval layer over indexed knowledge documents: vector scoring, multilingual lexical scoring, hybrid ranking, citation generation, retrieval trace persistence, and explicit no-source behavior.

This milestone turns Milestone 4 ingestion into a usable RAG foundation without adding LLM answer generation yet.

## Context
Relevant standing rules:
- Retrieval must be workspace-scoped before ranking.
- Japanese and Chinese retrieval must not rely only on whitespace tokenization.
- Retrieval calls must create `RetrievalTrace` rows.
- Retrieved results need citation metadata for later grounded answer generation.
- No-source cases must be explicit rather than silently returning weak evidence.
- No LLM calls are needed in this milestone.

Implemented foundation:
- Workspace auth and membership dependencies.
- Knowledge document upload/reindex.
- Document chunks with language and token counts.
- Mock embeddings stored in pgvector-compatible vector columns.

## Requirements
- Add SQLAlchemy models and migration for:
  - `RetrievalTrace`
  - `RetrievedChunk`
- Add retrieval API:
  - `POST /api/v1/workspaces/{workspace_id}/retrieval/search`
- Implement retrieval service with:
  - query language detection or explicit language input.
  - query embedding through the existing mockable `EmbeddingProvider`.
  - vector similarity scoring against stored chunk embeddings.
  - lexical scoring with word matching for English and character n-gram matching for Japanese/Chinese.
  - hybrid score combining vector and lexical scores.
  - metadata filters for `language` and optional `document_id`.
  - top-k limiting.
  - minimum-score no-source detection.
  - citation strings containing document title, version, chunk index, and chunk ID.
  - persisted retrieval trace and retrieved chunk rows.
- Ensure all retrieval candidates are filtered by `workspace_id` before scoring.
- Add tests for retrieval success, no-source, multilingual lexical behavior, trace persistence, and cross-workspace isolation.

## Non-goals
- No LangChain retriever wrapper yet unless it adds direct value.
- No LangGraph workflow integration.
- No answer generation.
- No context compression.
- No production search engine.
- No real embedding provider.
- No UI.

## Design Plan
- Add retrieval models to `backend/app/models/retrieval.py`.
- Add migration `0004_retrieval_traces.py`.
- Add schemas in `backend/app/schemas/retrieval.py`.
- Add retrieval service in `backend/app/services/retrieval_service.py`.
- Add lexical utilities in `backend/app/services/lexical_search.py`.
- Add API router `backend/app/api/v1/retrieval.py` and include it.
- Update model registry and test fixture imports.
- Update RAG/API/database/architecture docs and learning notes.

## Database Migrations
Create:
```text
RetrievalTrace
- id
- workspace_id
- graph_run_id nullable for future
- query
- language
- strategy
- filters_json
- latency_ms
- no_source
- created_at

RetrievedChunk
- id
- workspace_id
- retrieval_trace_id
- document_chunk_id
- rank
- vector_score nullable
- lexical_score nullable
- combined_score
- citation
```

## API Changes
Request:
```json
{
  "query": "返金は何日以内ですか？",
  "language": "ja",
  "top_k": 5,
  "min_score": 0.2,
  "document_id": null
}
```

Response:
```json
{
  "trace_id": "...",
  "language": "ja",
  "strategy": "hybrid",
  "no_source": false,
  "results": [
    {
      "chunk_id": "...",
      "document_id": "...",
      "document_title": "Refund Policy JA",
      "version": 1,
      "chunk_index": 0,
      "content": "...",
      "vector_score": 0.71,
      "lexical_score": 0.44,
      "combined_score": 0.60,
      "citation": "Refund Policy JA v1 #chunk-0 (...id...)"
    }
  ]
}
```

## Test Plan
Unit tests:
- English lexical score finds word overlap.
- Japanese/Chinese lexical score uses character n-grams.
- No-source threshold behavior works.

API/integration tests:
- upload docs, search, receive cited result.
- retrieval trace and retrieved chunk rows are persisted.
- language filter limits candidates.
- document filter limits candidates.
- no-source query returns empty results and `no_source=true` while still storing trace.
- user cannot retrieve chunks from another workspace.

Validation commands:
```bash
make backend-lint
make backend-test
make backend-migrate
make frontend-test
```

Docker smoke:
```bash
docker compose up --build -d api
# register, create workspace, upload document, search retrieval API
```

## Risks
- Mock embeddings are not semantically meaningful; hybrid retrieval must not pretend to prove production RAG quality.
- Python-side vector scoring is acceptable for local v1 but must move to pgvector SQL/index usage for larger datasets.
- Character n-gram lexical matching helps Japanese/Chinese but can create false positives.
- Returning full chunk content is acceptable for trace/debug v1, but later serving paths should context-pack within token budget.

## Acceptance Criteria
- Search returns cited chunks from the same workspace.
- Retrieval traces and retrieved chunks are stored.
- Cross-workspace retrieval is impossible.
- Japanese/Chinese lexical limitations are documented.
- No-source cases are explicit and tested.
- No LLM or real embedding provider calls are used.
- Validation passes.

## Human Review Checklist
- Confirm the retrieval result shape will support later citations in agent answers.
- Review whether Python-side scoring is acceptable for local v1.
- Check no-source threshold behavior.
- Inspect workspace isolation tests carefully.
- Confirm docs honestly state mock embedding limitations.

## Interview Notes
Be able to explain:
- Why retrieval traces matter for observability and debugging.
- How hybrid scoring combines semantic and lexical signals.
- Why CJK lexical matching needs character n-grams.
- Why no-source handling reduces hallucination risk.
- Why local Python scoring is a v1 tradeoff and how pgvector SQL indexes fit the scale path.


## Implementation Record
Completed implementation details:
- Added `backend/app/models/retrieval.py` with `RetrievalTrace` and `RetrievedChunk`.
- Added Alembic migration `0004_retrieval_traces.py`.
- Added `backend/app/services/lexical_search.py` and `backend/app/services/retrieval_service.py`.
- Added `backend/app/schemas/retrieval.py` and `backend/app/api/v1/retrieval.py`.
- Wired retrieval router and model registry.
- Added `backend/tests/test_retrieval.py`.
- Updated RAG, API, database schema, architecture-tree, and learning docs.

Important decisions:
- Keep vector scoring in Python for local v1; document pgvector SQL/index migration for scale.
- Use hybrid score with stronger lexical weight so policy terms and multilingual exact matches matter.
- Skip query embedding when no candidates exist after workspace/language/document filters.
- Return explicit `no_source=true` and store a trace for weak-evidence searches.

Validation results:
- `make backend-lint`: passed.
- `make backend-test`: 35 passed, 1 existing TestClient deprecation warning.
- `make frontend-test`: passed.
- `make backend-migrate`: passed against Docker PostgreSQL/pgvector.
- Docker API smoke: upload document, retrieval success, and no-source retrieval passed.

Self-review result:
- Fixed a PostgreSQL enum mismatch found by Docker smoke; SQLite tests did not catch this, so Docker validation remains mandatory for schema-touching milestones.
- No unresolved P0/P1 issues found.
- P2: retrieval scoring is local/Python-side and should move to pgvector SQL operators before larger datasets.
- P2: mock embeddings are deterministic but not semantic quality proof; evaluation must measure retrieval quality later.
