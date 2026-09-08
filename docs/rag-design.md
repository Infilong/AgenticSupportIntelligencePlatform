# RAG Design

## Agent knowledge access in the rebuild

Agent settings persist `knowledge_document_ids`: null or absent allows workspace knowledge;
an empty list allows none; up to 100 IDs restrict retrieval to selected documents. Updates
validate document ownership. Task admission snapshots the selection for that execution.
The graph passes this trusted setting into the search tool closure; it is not a model input.
Retrieval filters document IDs in SQL together with existing workspace, language and ready
version constraints before loading candidate content. Restricted traces record the filter.
No matching evidence routes to human review. Changing settings affects new requests only.

## Goal
Implement RAG with real quality controls for English, Japanese, and Chinese support workflows.

## Configured embeddings
`EMBEDDING_PROVIDER=mock` is the default. To opt into paid OpenAI embeddings, set it to `openai`,
supply `OPENAI_API_KEY`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`, and an explicit current
`EMBEDDING_TOKEN_COST_PER_1K`. PostgreSQL must be migrated through 0028. Missing key/price or
invalid dimensions fail configuration. Embedding HTTP uses the fixed official OpenAI endpoint;
the chat-provider `OPENAI_BASE_URL` does not redirect embedding traffic.
Indexing and queries share these settings. Reindex documents after changing provider/model/dimensions;
incompatible model rows are excluded and dimension mismatch fails explicitly. Configured indexing
batches already-chunked content and records each attempt independently of document transactions.
Oversized individual chunks fail before dispatch; text is not silently truncated.
Hybrid retrieval and the vector-only evaluation baseline use the configured vectors. Synthetic
HTTP integration tests prove orchestration/permissions/accounting, not real semantic quality.

## Current-version retrieval
On PostgreSQL, vector and hybrid searches rank candidates using pgvector cosine distance in
SQL. The shared candidate query applies workspace, selected-document, latest-version, language,
indexed-state and embedding-provider/model filters. SQL checks stored dimensions and nonzero
magnitude before query dispatch. Vector-only search fetches top-k; hybrid fetches at most
max(100, 10 * top-k) vector neighbors and applies the existing lexical blend to that pool.
Hybrid recall can differ from the former exhaustive blend and requires corpus evaluation.
No approximate index is introduced: this is exact database ranking with bounded transfer,
not proof of large-corpus latency. SQLite retains deterministic Python scoring for tests;
lexical-only search still loads its scoped candidate set and needs a bounded multilingual design.
The cosine operator follows the [pgvector documentation](https://github.com/pgvector/pgvector#querying).

Vector/hybrid scoring filters stored embeddings by the configured provider and model before
query dispatch. Both stored and query vectors must have configured dimensions, finite numeric
values and nonzero magnitude; invalid vectors raise an explicit retrieval error. With no
compatible candidates, retrieval returns no source without an embedding call. Lexical search
does not require model compatibility. This is a compatibility contract, not semantic quality;
see the [semantic retrieval plan](exec-plans/active/semantic-retrieval.md).

New searches select only the highest version number for each indexed document in the requested
workspace, before scoring. Language/document filters still apply. Reindexing retains historical
versions and trace references but excludes obsolete policy chunks from new model context.
A failed document is excluded rather than silently falling back to an older policy. This does
not solve concurrent reindexing, mock embedding quality or unbounded lexical candidate loading.
The default retrieval request selects lexical scoring when the configured embedding provider
is mock. SHA-derived mock vectors are not semantic evidence and do not contribute to relevance;
the query skips embedding generation, traces report `lexical`, and vector scores are null.
English token overlap with conservative plural normalization (`refunds`/`refund`, `policies`/
`policy`) and Japanese/Chinese character n-grams provide the actual ranking signal.
This cannot establish semantic relevance, handle synonyms reliably or prove factual support.

An injected non-mock embedding provider can use hybrid scoring. Evaluation's vector_rag baseline
explicitly selects vector-only scoring; its traces omit lexical scores. With the current mock
embedding runtime this remains a simulation, not a meaningful semantic-quality benchmark.
See [evaluation design](evaluation-design.md) for generation and mock limitations.

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
This sequence is the target architecture. Current indexing runs synchronously; a background
worker is not implemented. See the [code map](code-map.md) for runtime ownership.

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

Exact citation presence is separate from factual support. The graph additionally checks
[numeric durations](langgraph-workflow-design.md#numeric-duration-support) against the cited
packed text; values in uncited chunks or citation metadata do not count. This does not grade
general entailment, relations or negation.

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
- Revision 0027 stores embeddings in dimension-flexible pgvector `vector`; mocks still emit
  16 dimensions. Configured OpenAI indexing/query providers now use this storage; real semantic
  quality remains unverified by the synthetic integration tests.
- API upload and reindex index synchronously for local v1 while preserving a service boundary for future Redis workers.
- No LLM calls are used in ingestion, so raw documents cannot be sent to a model in this milestone.

Known limitations:
- Mock embeddings are not semantically meaningful; real multilingual embeddings are future provider work.
- Chunking is intentionally simple and must be evaluated before production use.
- Retrieval, lexical search, hybrid scoring, citations, and retrieval traces begin in Milestone 5.


## Implemented In Milestone 5
- Workspace-scoped retrieval API at `POST /api/v1/workspaces/{workspace_id}/retrieval/search`.
- `RetrievalTrace` and `RetrievedChunk` persistence for every search.
- Hybrid scoring with deterministic mock vector similarity plus lexical overlap.
- English lexical matching uses normalized word tokens.
- Japanese and Chinese lexical matching uses character bigrams/trigrams instead of whitespace-only tokenization.
- Citation strings include document title, version, chunk index, and chunk ID.
- No-source detection returns `no_source=true` while preserving a trace.
- If no candidates exist after workspace/language/document filters, the service skips query embedding to avoid unnecessary model work.

Known limitations:
- Vector scoring currently runs in Python for local v1. Production scale should use pgvector SQL operators and indexes.
- Mock embeddings are deterministic but not semantic quality evidence.
- Character n-grams can overmatch; evaluation must measure precision by language.
- Context packing/compression starts in later milestones.
