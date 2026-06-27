# LangChain and LangGraph Runtime Audit Correction

## Goal
Make LangChain and LangGraph usage visible, testable, and interview-defensible in the running product, not only in documentation.

## Context
The project already used LangGraph `StateGraph` for support-agent orchestration and LangChain Core for prompts, documents, runnables, and output parsing. The weak point was that this was hard to see from the product and the LangChain integration was too close to a prompt-wrapper layer.

## Implemented Correction
- Added a LangChain Core `StructuredTool` adapter named `search_documents` around workspace-scoped retrieval.
- Changed the `retrieve_evidence` LangGraph node to invoke that LangChain tool instead of calling retrieval directly.
- Added trace API runtime metadata for:
  - LangGraph orchestrator
  - `SupportAgentState` schema
  - graph builder
  - conditional routes
  - persistence records
  - LangChain components used in the workflow
- Added per-step metadata for runtime framework, node role, LangChain usage, and state keys.
- Added tool-call framework metadata to trace responses.
- Updated the Trace Explorer UI with an AI runtime panel and LangGraph/LangChain badges.
- Added tests proving runtime metadata and the LangChain `StructuredTool` retrieval step are present.

## Architecture Boundary
LangGraph owns graph orchestration and conditional routing.
LangChain owns prompt composition, document evidence objects, LCEL model-provider bridging, output parsing, and the retrieval tool adapter.
The backend still owns workspace permissions, persistence, graph trace records, AI run ledger rows, token/cost accounting, evaluation, and API boundaries.

## Why This Matters
Employers need to see that framework usage is not cosmetic. This correction makes the runtime inspectable from API and UI, and keeps important product controls outside black-box agent behavior.

## Risks And Follow-Up
- LangChain usage is now concrete but still conservative. Future improvements can add structured output schemas for classifier/drafter responses and a LangChain retriever abstraction with score metadata.
- LangGraph uses app-owned checkpoint rows instead of a LangGraph checkpointer. That is acceptable for this local-first portfolio slice, but the scale-path docs should explain when to adopt a LangGraph checkpointer backend.

## Verification
- `uv run ruff check .` -> passed
- `uv run pytest -s tests/test_langchain_support.py tests/test_agents.py` -> 17 passed
- `npm run test` -> passed
- `npm run build` -> passed
- `uv run pytest -s` -> 86 passed
- Docker rebuild: `docker compose up -d --build api frontend` -> passed
- Live HTTP smoke -> passed; run trace returned `LangGraph StateGraph` plus LangChain `StructuredTool search_documents` metadata
