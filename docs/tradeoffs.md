# Tradeoffs

## Local-First vs Cloud-First
Start local-first to keep the portfolio build achievable and reviewable. Document the Cloud Run and managed-service path, but do not implement cloud infrastructure in v1.

## PostgreSQL pgvector vs External Vector Database
Use pgvector in v1 because it keeps the stack simple and demonstrates practical backend ownership. Document a future dedicated vector index for larger scale.

## Hybrid RAG vs Pure Vector RAG
Hybrid retrieval is more work but better for support policies and multilingual exact-match terms. It also supports a stronger portfolio story around retrieval quality.

## LangGraph vs Free-Form Agent
Use LangGraph because the workflow must be stateful, inspectable, testable, and human-reviewable. Avoid uncontrolled autonomous agent behavior.

## Token Economy vs Model Quality
Use cheap models and deterministic code for routing and validation. Reserve stronger models for generation or judgment. Track cost so quality improvements can be compared against spend.

## Simple UI vs Beautiful UI
The frontend should be professional and clear, but Phase 1 prioritizes traceability, evaluation, and cost visibility over complex visual design.

## Broad Feature Set vs Vertical Slice
Prefer a small, correct vertical slice with tests and traceability over many shallow features.
