# Architecture

## Overview
The system is a local-first AI support intelligence platform. Phase 1 uses a single FastAPI backend, a TypeScript frontend, PostgreSQL with pgvector, Redis-backed workers, Docker Compose, LangChain, and LangGraph.

The architecture is modular so the system starts small but can later scale without rewriting ownership boundaries or API contracts.

## Recommended Tech Stack

Backend:
- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- pgvector
- Redis
- Celery, RQ, or Arq
- pytest
- ruff
- mypy or pyright if manageable

Frontend:
- Next.js or React
- TypeScript
- simple internal product-style UI
- Tailwind or clean component library

AI layer:
- LangChain
- LangGraph
- OpenAI-compatible model provider abstraction
- Gemini provider optional
- mock LLM provider for tests
- embedding provider abstraction

DevOps:
- Docker Compose
- GitHub Actions CI
- Makefile
- `.env.example`
- seed/demo data
- structured README

## Pillar 1: Multilingual Data Platform
Responsible for dataset import, import batches, conversation examples, messages, language detection, label editing, and eval-ready example selection.

Modules:
```text
datasets
imports
examples
messages
language
labels
```

## Pillar 2: Knowledge And Retrieval
Responsible for knowledge document upload, document versioning, parsing, language-aware chunking, embeddings, vector search, lexical search, hybrid retrieval, citation metadata, retrieval trace, and context packing/compression.

Modules:
```text
documents
chunks
embeddings
retrieval
context_packing
citations
```

## Pillar 3: Agent Workflow
Responsible for LangGraph execution, graph state, graph steps, tool execution, conditional routing, human review, checkpoints, and workflow resume.

Modules:
```text
agents
graph_runtime
tools
human_review
checkpoints
```

## Pillar 4: Quality And Safety
Responsible for guardrails, no-source refusal, prompt injection checks, policy/tone checks, confidence scoring, evaluation cases, evaluation runs, per-language metrics, and permission leakage tests.

Modules:
```text
guardrails
evaluation
rubrics
safety
quality
```

## Pillar 5: Observability And Cost
Responsible for AI run ledger, token usage, estimated cost, latency, model choice, cache hit rate, audit logs, dashboard summaries, and trace inspection.

Modules:
```text
ai_runs
token_accounting
costs
audit_logs
observability
cache
```

## Boundary Rules
LangChain must not hide the project architecture. LangGraph must not become an uncontrolled autonomous agent. Backend services own permission checks, persistence, auditability, evaluation, token accounting, and traceability.

## Related Design Docs
- `docs/database-schema.md`
- `docs/api-design.md`
- `docs/rag-design.md`
- `docs/langgraph-workflow-design.md`
- `docs/tool-execution-design.md`
- `docs/token-economy-design.md`
- `docs/evaluation-design.md`
- `docs/security-threat-model.md`
- `docs/observability-design.md`
- `docs/scale-path.md`
- `docs/tradeoffs.md`
