# Repository Instructions

## Project
Multilingual Agentic Support Intelligence Platform is a serious mid-to-senior AI/backend portfolio project. It must look like a small but production-minded internal AI platform, not a tutorial chatbot.

V1 supports English, Japanese, and Chinese. It starts local-first for a small team and documents a future scale path without pretending to implement enterprise infrastructure in v1.

## Context Loading
Codex loads this file automatically. Keep other context selective:
- Read `docs/README.md` first when choosing which docs apply.
- Read `docs/PROJECT_CONTEXT.md` for almost every real implementation task.
- Read `docs/architecture-tree.md` for quick architecture/tool orientation.
- Read `docs/PLANS.md` only when creating a ticket plan.
- Read `docs/milestone-plan.md` only for milestone sequencing or scope checks.
- Read focused design docs only when the task touches that subsystem.
- Do not read every doc by default; preserve context for implementation and verification.

## Operating Rules
- Plan before coding complex tasks.
- Implement one focused ticket at a time.
- Keep diffs small and reviewable.
- Do not implement broad milestones in one pass.
- Do not add unrelated refactors.
- Do not create fake implementations that only look complete.
- Do not hide errors with broad exception handling.
- Ask clarifying questions only when a decision blocks implementation.
- Prefer a small, correct vertical slice over broad shallow features.

## Architecture Rules
- Backend owns database schema, permission checks, trace persistence, AI run ledger, evaluation logic, token accounting, audit logs, and API boundaries.
- LangChain is used for model abstraction, prompt templates, structured outputs, retrievers, tools, and document loaders when useful.
- LangGraph is used for inspectable stateful workflows, conditional routing, checkpointing, and human review.
- Every workspace-owned entity must include `workspace_id`.
- Every workspace-scoped operation must enforce permission checks.
- Every model call must create an AI run ledger record.
- Every graph node execution must create graph trace data.
- Every retrieval call must create retrieval trace data.

## AI And Token Rules
- Token economy is a first-class requirement.
- Use deterministic code before LLM calls whenever possible.
- Never send raw long documents to models.
- Use retrieval, filtering, reranking, compression, caching, and token budgeting before model calls.
- Use mock LLM and embedding providers in automated tests.

## Security Review Rules
Verify:
- every protected route has authentication.
- workspace isolation is enforced.
- retrieval cannot leak another workspace's chunks.
- no secrets are hardcoded.
- PII is not logged.
- prompt injection and unsafe tool calls are handled.

## Testing Rules
Every feature must include tests. Cover happy paths, failure paths, and permission denial. Use mock providers for LLM responses, embeddings, token counts, latency simulation, and error simulation.

## Documentation Rules
Update docs when architecture, APIs, workflows, or evaluation behavior changes. Add or update learning notes after each milestone.

## Commands
Milestone 1 must finalize these commands:

```bash
make setup
make backend-test
make backend-lint
make frontend-test
make frontend-build
docker compose up --build
```

## Definition Of Done
A feature is not done until requirements are implemented, non-goals are respected, tests pass, workspace permissions are checked, errors are explicit, docs are updated if needed, learning notes are added when relevant, and self-review has no unresolved P0/P1 issues.
