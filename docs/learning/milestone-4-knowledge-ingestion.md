# Milestone 4: Knowledge Document Ingestion

## What Was Built
Milestone 4 added workspace-scoped knowledge document ingestion:
- upload, list, detail, and reindex APIs.
- `KnowledgeDocument`, `DocumentVersion`, `DocumentChunk`, and `Embedding` tables.
- deterministic text/markdown parsing.
- language-aware chunking for English, Japanese, and Chinese.
- an `EmbeddingProvider` abstraction with a deterministic mock embedding provider.
- PostgreSQL pgvector storage for mock vectors.
- tests for parsing, chunking, embeddings, upload, reindex, failure status, and workspace isolation.

## Why Companies Care
Real AI products need a reliable ingestion pipeline before they can build RAG. Employers care that documents are versioned, chunked, embedded, isolated by tenant/workspace, and testable without calling expensive external models. This is also where token economy begins: long documents are prepared for retrieval instead of being sent raw to an LLM.

## How This Project Uses It
The platform stores support policies, FAQs, release notes, and manuals as versioned knowledge documents. Each upload creates chunks and embeddings that Milestone 5 will search. The current implementation indexes synchronously for local v1, but the work is isolated in `KnowledgeService` so it can move behind Redis workers later.

## Design Tradeoffs
- Synchronous indexing is simpler for local v1 and easier to test, but large production uploads should become background jobs.
- Mock embeddings make tests deterministic and free, but they do not represent semantic search quality.
- English chunking uses word windows; Japanese and Chinese use character windows because whitespace tokenization is unreliable.
- Raw text is stored in PostgreSQL for local development. A production version may move raw files to object storage and keep metadata in the database.
- The mock vector dimension is `16` to keep local storage small. A real provider will require a migration to the provider's embedding dimension.

## Failure Modes
- Forgetting `workspace_id` filters can leak documents or chunks across workspaces.
- Treating mock embedding quality as real retrieval quality would be a fake implementation.
- Sending raw documents to an LLM during ingestion would violate token-economy rules.
- Reindexing by mutating old chunks would destroy auditability; versioning preserves history.
- Japanese and Chinese chunking can split semantic units awkwardly, so evaluation must catch retrieval quality issues later.

## Interview Explanation
“I separated document ingestion from retrieval. Upload creates a workspace-scoped document, immutable document version, chunks, and mock embeddings. The embedding provider is abstracted so tests never call real AI services, and PostgreSQL uses pgvector storage so the schema matches the future retrieval system. For token economy, ingestion never calls an LLM and long documents are chunked before any AI workflow can use them. The local version indexes synchronously for simplicity, but the service boundary is ready to move to a Redis worker.”

## Review Checklist
- Verify every document query filters by `workspace_id`.
- Verify unsupported file types fail explicitly.
- Verify reindex creates a new version.
- Verify tests use mock embeddings only.
- Verify no LLM dependency exists in ingestion.
