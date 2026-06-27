# Milestone 6: AI Run Ledger And Token Budget Planner

## Goal
Create the observability and token-economy foundation for future LLM workflows: model configs, AI run ledger, cost estimation, token budget planning, cache entries, a mock model provider, and a workspace-scoped cost summary API.

This milestone should not add LangGraph or answer generation yet. It creates the backend contracts that Milestone 7 will use.

## Context
Relevant standing rules:
- Token economy is first-class.
- Every model call must be token/cost/latency trackable.
- Tests must use mock providers.
- Workspace-scoped cost views must enforce membership.
- Deterministic code should run before model calls.

Current foundation:
- Knowledge ingestion uses mock embeddings.
- Retrieval uses mock query embeddings and skips embedding if there are no candidates.
- No LLM provider or AI run ledger exists yet.

## Requirements
- Add SQLAlchemy models and Alembic migration for:
  - `ModelConfig`
  - `PromptTemplate`
  - `AIRun`
  - `CacheEntry`
- Add token/cost utilities:
  - deterministic token estimator.
  - model pricing lookup.
  - cost calculator.
- Add `TokenBudgetPlanner` that decides:
  - max retrieved chunks.
  - whether compression is needed.
  - whether cache should be used.
  - whether a cheaper model should be selected.
  - whether the request exceeds budget.
  - whether to route to human review due to high estimated cost.
- Add mock model provider that records an `AIRun` for each call.
- Add cost summary API:
  - `GET /api/v1/workspaces/{workspace_id}/costs/summary`
- Ensure all AI run and cost queries filter by `workspace_id`.
- Add tests for AI run recording, cost calculation, budget decisions, cache entry uniqueness, and workspace isolation.

## Non-goals
- No LangGraph workflow yet.
- No real OpenAI/Gemini provider.
- No answer generation endpoint.
- No frontend cost dashboard.
- No prompt management UI.
- Do not retrofit all prior embedding calls unless doing so stays small and testable.

## Design Plan
- Add `backend/app/models/ai.py`.
- Add `backend/app/schemas/costs.py` and possibly `backend/app/schemas/ai.py`.
- Add `backend/app/services/token_accounting.py`.
- Add `backend/app/services/token_budget.py`.
- Add `backend/app/services/model_provider.py` with `MockModelProvider`.
- Add `backend/app/services/cost_service.py`.
- Add `backend/app/api/v1/costs.py`.
- Add migration `0005_ai_observability.py`.
- Update router, model registry, tests, docs, and learning note.

## Database Migrations
Create:
```text
ModelConfig
- id
- workspace_id nullable
- provider
- model
- purpose
- prompt_token_cost_per_1k
- completion_token_cost_per_1k
- max_context_tokens
- active
- created_at

PromptTemplate
- id
- workspace_id
- name
- language
- version
- template_text
- active
- created_at

AIRun
- id
- workspace_id
- graph_run_id nullable
- graph_step_id nullable
- provider
- model
- purpose
- language
- prompt_template_id nullable
- prompt_version nullable
- prompt_tokens
- completion_tokens
- total_tokens
- estimated_cost
- latency_ms
- cache_hit
- status
- error_message nullable
- created_at

CacheEntry
- id
- workspace_id
- cache_key
- purpose
- language nullable
- value_json
- token_count
- expires_at nullable
- created_at
```

## API Changes
`GET /api/v1/workspaces/{workspace_id}/costs/summary` returns totals by workspace:
```json
{
  "workspace_id": "...",
  "total_runs": 12,
  "total_tokens": 12345,
  "total_estimated_cost": 0.42,
  "average_latency_ms": 220,
  "cache_hit_rate": 0.25,
  "by_purpose": [
    {"purpose": "classification", "runs": 5, "tokens": 1200, "estimated_cost": 0.01}
  ]
}
```

## Test Plan
Unit tests:
- token estimator is deterministic.
- cost estimator handles prompt and completion tokens.
- classification selects cheaper model config than final answer.
- budget planner denies over-budget requests.
- budget planner recommends compression for large contexts.

Integration tests:
- mock model provider records an `AIRun` on success.
- mock model provider records failed `AIRun` on provider error.
- cost summary aggregates only current workspace.
- another workspace cannot view cost summary for a workspace they do not belong to.
- cache entries are unique by workspace/cache key/purpose.

Validation commands:
```bash
make backend-lint
make backend-test
make backend-migrate
make frontend-test
```

## Risks
- Fake implementation risk: cost accounting must create real persisted rows, not just return numbers.
- Pricing accuracy risk: built-in prices are estimates for portfolio/demo only and must be documented.
- Scope risk: integrating every existing embedding path into the ledger could distract from creating the ledger contract. Prefer making the provider wrapper correct and plan retrofits as needed.
- Security risk: prompt or cache data can contain sensitive content. Do not log secrets; keep cost summary aggregate.

## Acceptance Criteria
- Every mock model provider call creates an `AIRun`.
- Token/cost/latency fields are recorded.
- Budget enforcement works.
- Long context planning triggers compression/denial decisions before model call.
- Cost summary is workspace-scoped.
- Tests pass and use mock providers only.

## Human Review Checklist
- Check whether the `AIRun` schema will support LangGraph trace linkage.
- Confirm token/cost estimates are clearly labeled estimates.
- Verify cost summary cannot leak another workspace.
- Review planner decisions for interview defensibility.
- Confirm no real model provider is introduced.

## Interview Notes
Be able to explain:
- Why AI run ledgers are required for production LLM systems.
- How token budgeting protects cost and latency.
- Why tests use mock providers.
- How workspace isolation applies to observability data.
- Why model pricing is versioned/configurable instead of hardcoded everywhere.


## Implementation Record
Completed implementation details:
- Added `backend/app/models/ai.py` with `ModelConfig`, `PromptTemplate`, `AIRun`, and `CacheEntry`.
- Added Alembic migration `0005_ai_observability.py`.
- Added `token_accounting.py`, `token_budget.py`, `model_provider.py`, and `cost_service.py`.
- Added `GET /api/v1/workspaces/{workspace_id}/costs/summary`.
- Added `backend/tests/test_ai_observability.py`.
- Updated API, architecture, database, observability, token economy, and learning docs.

Important decisions:
- Use a ledger-aware mock model provider and postpone real providers.
- Record failed model calls as `AIRun` rows.
- Treat costs as estimates and document that clearly.
- Keep embedding retrofits out of this milestone to keep the ledger contract focused and reviewable.

Validation results:
- `make backend-lint`: passed.
- `make backend-test`: 41 passed, 1 existing TestClient deprecation warning.
- `make backend-migrate`: passed against Docker PostgreSQL/pgvector.
- Docker API smoke: mock AI run inserted through service and cost summary endpoint returned aggregate usage.

Self-review result:
- No unresolved P0/P1 issues found.
- P2: exact provider tokenizers are not used yet; current estimator is deterministic and approximate.
- P2: existing embedding paths are not yet ledger-aware. Future provider-wrapper work should address this before production claims.
- P2: API still uses FastAPI `detail` errors instead of the documented unified error envelope.
