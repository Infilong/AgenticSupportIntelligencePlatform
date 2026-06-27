# Milestone 5: Retrieval And Citations

## What Was Built
Milestone 5 added the first retrieval layer:
- `POST /api/v1/workspaces/{workspace_id}/retrieval/search`.
- `RetrievalTrace` and `RetrievedChunk` tables.
- vector similarity over stored mock embeddings.
- lexical matching for English, Japanese, and Chinese.
- hybrid ranking.
- citation generation.
- no-source detection.
- tests for trace persistence, filters, no-source behavior, and workspace isolation.

## Why Companies Care
RAG quality is not just “call a vector database.” Companies need retrieval that is inspectable, tenant-safe, multilingual, and measurable. Traces let engineers debug why an answer used certain evidence. Citations make generated answers reviewable. No-source behavior reduces hallucination risk.

## How This Project Uses It
The platform searches workspace-owned document chunks and returns cited evidence for future LangGraph agent steps. The result shape already includes document title, version, chunk index, scores, content, and citation text so later agent responses can stay grounded.

## Design Tradeoffs
- Python-side vector scoring is acceptable for local v1 and simple tests, but production scale should push vector search into PostgreSQL pgvector indexes.
- Mock embeddings are deterministic and free but do not prove semantic retrieval quality.
- Hybrid scoring weights lexical overlap strongly so exact policy terms, dates, and CJK n-grams matter.
- Japanese/Chinese lexical search uses character n-grams because whitespace tokenization is unreliable.
- If no candidates exist after filters, the service skips query embedding to avoid unnecessary model work.

## Failure Modes
- Missing `workspace_id` filters would leak chunks across workspaces.
- Treating mock embeddings as production-quality semantic search would be misleading.
- Too low a no-source threshold can return weak evidence; too high a threshold can hide useful evidence.
- Character n-grams can create false positives in Japanese/Chinese.
- Returning too many chunks later can waste tokens; context packing must enforce budgets in future milestones.

## Interview Explanation
“I implemented retrieval as an inspectable service, not just a vector search call. Every search creates a retrieval trace, candidates are filtered by workspace before scoring, and results include citations that identify the source document, version, and chunk. The local v1 combines deterministic mock vector similarity with lexical matching, including character n-grams for Japanese and Chinese. No-source cases are explicit and still traced, which is important for RAG safety and debugging.”

## Review Checklist
- Verify retrieval filters by workspace before scoring.
- Verify no-source searches still persist traces.
- Verify citations include enough source metadata.
- Verify Japanese/Chinese matching does not rely only on spaces.
- Verify no real AI provider is called in tests.
