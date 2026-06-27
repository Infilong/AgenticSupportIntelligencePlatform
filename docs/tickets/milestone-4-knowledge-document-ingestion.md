# Milestone 4: Knowledge Document Ingestion

## Goal
Build the first knowledge-ingestion slice: workspace-scoped document upload, document versions, language-aware chunking, mockable embedding generation, persisted chunk embeddings, and status tracking.

This milestone prepares the system for retrieval in Milestone 5 without adding retrieval search yet.

## Context
Relevant standing rules:
- `AGENTS.md`: workspace isolation, mock providers in tests, no fake implementations, no raw long documents sent to models.
- `docs/PROJECT_CONTEXT.md`: token economy, multilingual support, workspace isolation, observability, interview-defensible decisions.
- `docs/rag-design.md`: document flow, multilingual chunking, embeddings, later retrieval/citations.
- `docs/database-schema.md`: `KnowledgeDocument`, `DocumentVersion`, `DocumentChunk`, `Embedding` starting entities.
- `docs/api-design.md`: workspace-scoped knowledge-document routes.

Current implemented foundation:
- FastAPI API, SQLAlchemy, Alembic, pytest, ruff.
- Auth, JWT, workspace membership dependency.
- Dataset import and deterministic language detection for `en`, `ja`, `zh`.

## Requirements
- Add SQLAlchemy models and Alembic migration for:
  - `KnowledgeDocument`
  - `DocumentVersion`
  - `DocumentChunk`
  - `Embedding`
- Every new table must include `workspace_id` and workspace foreign keys.
- Add upload/list/detail/reindex API routes:
  - `POST /api/v1/workspaces/{workspace_id}/knowledge-documents`
  - `GET /api/v1/workspaces/{workspace_id}/knowledge-documents`
  - `GET /api/v1/workspaces/{workspace_id}/knowledge-documents/{document_id}`
  - `POST /api/v1/workspaces/{workspace_id}/knowledge-documents/{document_id}/reindex`
- Accept text/markdown/plain policy documents as text payloads in v1; reject unsupported file types.
- Detect or accept document language for `en`, `ja`, `zh`.
- Parse raw text deterministically. No LLM calls.
- Chunk documents with language-aware behavior:
  - English can split on words/sentences.
  - Japanese/Chinese must not rely only on whitespace; use character windows with overlap.
- Generate embeddings through an `EmbeddingProvider` abstraction.
- Use a deterministic `MockEmbeddingProvider` by default for local/test execution.
- Persist embedding vectors for each chunk. PostgreSQL migration must use pgvector storage; tests may use JSON-compatible storage through SQLAlchemy type fallback.
- Track document status transitions: pending/indexing/indexed/failed.
- Reindex should create a new document version and replace active chunk/embedding rows for the document through versioning, not mutate old version content.
- Ensure long documents are never sent to an LLM. This milestone must not introduce LLM providers.

## Non-goals
- No retrieval/search endpoint implementation; that is Milestone 5.
- No LangChain retriever integration yet.
- No LangGraph workflow changes.
- No real OpenAI/Gemini embedding provider yet.
- No object storage; raw text can be stored in the database for local v1.
- No PDF/DOCX parsing in this milestone.
- No frontend UI changes unless required for build stability.

## Design Plan
- Add `backend/app/models/knowledge.py` with document/version/chunk/embedding models and enums.
- Add `backend/app/schemas/knowledge.py` with request/response schemas.
- Add `backend/app/services/document_parser.py` for supported content-type validation and deterministic text normalization.
- Add `backend/app/services/chunking.py` for language-aware chunking.
- Add `backend/app/services/embedding_provider.py` for provider interface and mock provider.
- Add `backend/app/services/knowledge_service.py` for upload, indexing, list/detail, and reindex operations.
- Add `backend/app/api/v1/knowledge.py` and include it in the v1 router.
- Add Alembic migration `0003_knowledge_ingestion.py`.
- Update model registry and test fixtures.
- Add demo docs under `backend/demo_data/knowledge/`.
- Update `docs/architecture-tree.md`, `docs/database-schema.md`, `docs/api-design.md`, and `docs/learning/milestone-4-knowledge-ingestion.md`.

## Database Migrations
Create tables:
- `knowledge_documents`
- `document_versions`
- `document_chunks`
- `embeddings`

Important fields:
- `workspace_id` on all tables.
- `KnowledgeDocument.status` enum.
- `DocumentVersion.version`, `content_hash`, `raw_text`.
- `DocumentChunk.chunk_index`, `content`, `token_count`, `metadata_json`.
- `Embedding.provider`, `model`, `vector`.

For PostgreSQL, use `vector(16)` for mock embeddings in v1. The embedding dimension is intentionally small for local tests and can migrate later with a real provider. In SQLite tests, store the vector through a compatible JSON/text type.

## API Changes
All routes are authenticated and workspace-scoped.

Upload request:
```json
{
  "title": "Refund Policy JP",
  "content_type": "text/markdown",
  "content": "...",
  "language": "ja"
}
```

Upload response includes document metadata, latest version, chunk count, embedding count, and status.

## Test Plan
Unit tests:
- supported/unsupported content-type parsing.
- language-aware chunking for English, Japanese, Chinese.
- mock embedding provider returns deterministic vectors with expected dimensions.
- long documents are chunked and never passed to any LLM path.

API/service tests:
- upload creates document, version, chunks, embeddings.
- language is stored on document and chunks.
- unsupported file type returns 400.
- list/detail are workspace-scoped.
- cross-workspace document detail is denied/not found.
- reindex creates a new version and new chunks/embeddings.
- indexing failure marks document failed and stores error.

Validation commands:
```bash
make backend-lint
make backend-test
make backend-migrate
```

If Docker is available:
```bash
docker compose up --build -d
curl http://127.0.0.1:8000/health
```

## Risks
- pgvector portability: SQLite tests do not support pgvector, so the SQLAlchemy type must be compatible in tests while the Alembic migration creates real pgvector storage in PostgreSQL.
- Fake worker risk: v1 may use synchronous indexing behind the upload route. This is acceptable only if documented as local-first; later Redis worker extraction must keep the same service boundary.
- Overreach risk: adding retrieval in this milestone would blur scope.
- Token-economy risk: raw documents must not be sent to an LLM; this milestone should not introduce an LLM dependency.
- Multilingual quality risk: simple chunking for Japanese/Chinese is not production-grade; document limitations and keep interfaces replaceable.

## Acceptance Criteria
- Upload creates workspace-scoped document, version, chunks, and embeddings.
- Document status updates to indexed or failed.
- Unsupported file types are rejected.
- Reindex creates a new version.
- Long documents are chunked before embedding.
- Tests cover worker/index success, failure, chunking, embeddings, and permissions.
- No real AI provider calls are used.
- Validation passes.

## Human Review Checklist
- Confirm the API surface is understandable and workspace-scoped.
- Check whether synchronous local indexing is acceptable for v1.
- Confirm the mock embedding dimension and fallback vector storage are explained.
- Verify there is no LLM path in ingestion.
- Review chunking limitations for Japanese/Chinese.
- Review tests for cross-workspace leakage.

## Interview Notes
Be able to explain:
- Why ingestion is separated from retrieval.
- Why embedding providers are abstracted and mocked in tests.
- Why local v1 can index synchronously while preserving a future worker boundary.
- How language-aware chunking differs for English vs Japanese/Chinese.
- How workspace isolation is enforced at model, service, and API levels.
- How this milestone supports later RAG quality, citations, token budgeting, and LangGraph traces.


## Implementation Record
Completed implementation details:
- Added `backend/app/models/knowledge.py` with document, version, chunk, embedding, status enum, and vector type.
- Added `backend/app/api/v1/knowledge.py` and included it in the v1 router.
- Added `backend/app/services/document_parser.py`, `chunking.py`, `embedding_provider.py`, and `knowledge_service.py`.
- Added `backend/app/schemas/knowledge.py`.
- Added Alembic migration `0003_knowledge_ingestion.py` with pgvector `vector(16)` storage.
- Added `backend/tests/test_knowledge_documents.py`.
- Updated architecture, RAG, API, database schema docs, and learning notes.

Important decisions:
- Use synchronous indexing in local v1, but keep ingestion behind `KnowledgeService` so a Redis worker can call the same boundary later.
- Use deterministic mock embeddings only in this milestone.
- Keep PDF/DOCX parsing postponed; v1 accepts text and markdown payloads.
- Store old chunks by document version instead of mutating them during reindex.

Validation results:
- `make backend-lint`: passed.
- `make backend-test`: 29 passed, 1 existing TestClient deprecation warning.
- `make frontend-test`: passed.
- `make backend-migrate`: passed against Docker PostgreSQL/pgvector after fixing enum idempotency.

Self-review result:
- No unresolved P0/P1 issues found.
- P2: API error response still uses FastAPI `detail` shape instead of the documented unified `error` shape. This pre-existing inconsistency should be handled in a future API consistency ticket.
- P2: synchronous indexing is acceptable for local v1 but must become a real background worker before large-document usage.
