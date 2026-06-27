# RAG Design

## Goal
Implement RAG with real quality controls for English, Japanese, and Chinese support workflows.

## Required Capabilities
- document upload
- parsing
- language-aware chunking
- embedding generation
- pgvector storage
- vector search
- lexical search
- hybrid retrieval
- metadata filtering
- citation generation
- retrieval trace
- no-source refusal
- token-budget-aware context packing

## Document Flow
1. User uploads a knowledge document in a workspace.
2. System creates a `KnowledgeDocument` and `DocumentVersion`.
3. Background worker parses raw text.
4. Language-aware chunker creates `DocumentChunk` rows.
5. Embedding provider creates embeddings for chunks.
6. Retrieval APIs search chunks by workspace, language, metadata, vector score, and lexical score.
7. Retrieval result creates `RetrievalTrace` and `RetrievedChunk` rows.

## Multilingual Retrieval
English, Japanese, and Chinese must all work in v1.

For Japanese and Chinese, do not rely only on whitespace tokenization. Initial implementation can use:
- multilingual embeddings
- normalized substring matching
- character n-gram matching
- documented limitations

Design retrieval interfaces so a production-grade search engine can replace the simple lexical component later.

## Citation Requirements
Each retrieved chunk should expose source document, document version, chunk ID, language, rank, scores, and citation string. Generated answers must cite retrieved evidence where claims depend on company knowledge.

## No-Source Refusal
If retrieval cannot find sufficient support, the workflow should refuse or route to human review rather than hallucinate.

## Token Economy
RAG must not pass all retrieved text to the model. Context packing should select only the most relevant chunks within token budget and trigger compression when needed.


## Implemented In Milestone 4
- Workspace-scoped `KnowledgeDocument`, `DocumentVersion`, `DocumentChunk`, and `Embedding` tables.
- Plain-text and markdown parsing only; PDF/DOCX are intentionally postponed.
- Deterministic language-aware chunking:
  - English uses word windows with overlap.
  - Japanese and Chinese use character windows with overlap because whitespace is unreliable.
- `EmbeddingProvider` abstraction with deterministic `MockEmbeddingProvider` for tests/local development.
- PostgreSQL migration stores embeddings in pgvector `vector(16)` for the mock provider.
- API upload and reindex index synchronously for local v1 while preserving a service boundary for future Redis workers.
- No LLM calls are used in ingestion, so raw documents cannot be sent to a model in this milestone.

Known limitations:
- Mock embeddings are not semantically meaningful; real multilingual embeddings are future provider work.
- Chunking is intentionally simple and must be evaluated before production use.
- Retrieval, lexical search, hybrid scoring, citations, and retrieval traces begin in Milestone 5.
