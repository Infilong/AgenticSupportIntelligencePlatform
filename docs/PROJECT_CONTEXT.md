# Project Context

This is the concise standing context to read before most tasks. Detailed rules live in focused design docs.

## Product
Build the Multilingual Agentic Support Intelligence Platform: a local-first internal AI platform for multilingual support, product, and community workflows. It imports English/Japanese/Chinese conversations, curates labels, indexes knowledge documents, runs a LangGraph support-agent workflow with RAG and human review, evaluates output quality per language, and tracks every model call for token cost, latency, cache use, and quality.

## Primary Goal
Demonstrate production-style AI/backend engineering:
- backend architecture
- multilingual AI systems
- dataset curation
- RAG quality
- LangChain usage
- LangGraph orchestration
- human review
- guardrails
- evaluation
- token economy
- observability
- auditability
- permission isolation
- Docker-based local deployment
- clean documentation
- production-defensible decisions

## First-Class Requirements
- Token economy is first-class.
- Multilingual support is first-class.
- Workspace isolation is first-class.
- Evaluation is first-class.
- Observability is first-class.
- Every feature should have clear rationale, tradeoffs, and operational behavior.

## Supported Languages
V1 supports `en`, `ja`, and `zh`. Future languages must be added through language configuration, prompt templates, chunking strategy, and evaluation rubrics rather than invasive rewrites.

## Non-Negotiable AI Rules
- Use deterministic code before LLM calls when possible.
- Do not use an LLM for simple parsing, routing, formatting, or validation if normal code is enough.
- Avoid sending raw long documents to models.
- Use retrieval, filtering, reranking, compression, and caching before model calls.
- Track prompt tokens, completion tokens, total tokens, model, provider, latency, estimated cost, cache hit rate, language, graph run, graph step, and evaluation result for every AI run.
- Tests must use mock LLM and embedding providers.

## Non-Negotiable Workspace Rules
- Every workspace-owned entity has `workspace_id`.
- A user must not access, retrieve, evaluate, or view data from a workspace they do not belong to.
- Permission denial must be tested for documents, datasets, examples, labels, graph runs, human reviews, evaluations, cost summaries, and audit logs.


## Resource And File Management Rules
- Upload/import is never a complete resource workflow by itself. User-owned resources must have permission-gated list, detail, edit or reindex, move, and delete paths where deletion is safe for the domain.
- Growing collections such as knowledge documents, datasets, imports, and future file-backed resources must not render as unbounded flat lists in the frontend. Use folders, search, filters, bounded/paginated lists, and detail inspectors.
- Folder IDs and resource IDs are workspace-scoped. Cross-workspace folder assignment, move, delete, and retrieval must be rejected by the backend.
- Frontend permission states are explanatory only; the backend must enforce create, move, edit, delete, and folder-management permissions.
- Large source content and indexed chunks belong in bounded inspectors or detail panels, not expanding page sections that grow with every file name or chunk.

## Human And Codex Roles
The human engineer owns requirements, scope decisions, architecture approval, code review, test review, final merge decisions, project narrative, and quality bar.

Codex assists with planning, boilerplate, implementation, tests, debugging, docs, refactoring, code review, and explaining code.

## Working Loop
For each milestone or feature: plan, update architecture docs, break into tickets, implement one small ticket, add tests, run validation, explain the diff, update learning notes, self-review, then stop for human review.
