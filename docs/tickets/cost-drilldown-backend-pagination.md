# Cost Drilldown Backend Pagination

## Goal
Keep token/cost observability usable as graph runs and AI ledger rows grow. The cost page should preserve full workspace accounting totals, but drilldown lists must be backend-filtered and paginated instead of loaded as broad recent arrays and sliced in the browser.

## Context
Token economy is a first-class project requirement. The cost dashboard already summarized workspace totals, budgets, latency, cache hit rate, agent attribution, model attribution, graph-run spend, and AI run ledger rows. The remaining scale issue was that recent graph-run spend and recent AI ledger rows were limited server-side but searched and paged only locally.

## Requirements
- Preserve full workspace accounting totals and budget posture.
- Add backend query support for cost drilldown search.
- Add graph-run status filtering for run-level spend.
- Add AI run status filtering for ledger rows.
- Add separate backend `limit` and `offset` controls for graph-run spend and AI ledger rows.
- Keep search workspace-scoped and able to match agent/model/purpose/run/status/error fields.
- Wire frontend page controls to backend-loaded slices.

## Non-goals
- No schema changes.
- No deletion for cost or AI run ledger rows; they are observability evidence.
- No total-count endpoint in this ticket.
- No changes to budget enforcement.

## Implementation Notes
- `GET /costs/summary` now accepts `search`, `graph_run_status`, `ai_run_status`, `graph_run_limit`, `graph_run_offset`, `ai_run_limit`, and `ai_run_offset`.
- `CostService.summarize_workspace()` keeps totals unfiltered while applying filters only to `recent_runs` and `recent_ai_runs`.
- AI ledger search joins graph runs and agents so agent-name search still works after backend filtering.
- The frontend keeps local filtering for aggregate cards, but graph-run spend and AI ledger rows are now backend-loaded pages.
- Search resets both cost drilldown pages; status filters reset the relevant page.

## Validation
- `cd backend && uv run ruff check app/api/v1/costs.py app/services/cost_service.py tests/test_ai_observability.py` -> passed.
- `cd backend && uv run pytest -s -q tests/test_ai_observability.py tests/test_budget_policies.py` -> 14 passed, 1 warning.
- `cd frontend && npm run typecheck` -> passed.
- `cd frontend && npm run build` -> passed.
- `git diff --check` -> passed.

## Human Review Checklist
- Confirm cost totals do not change when search/status filters are applied.
- Confirm graph-run spend Next/Previous behaves clearly with full pages.
- Confirm AI ledger search can find agent names, model names, purposes, statuses, run IDs, and errors.
- Confirm cost rows still link back to trace inspection.

## Interview Notes
This ticket demonstrates the token-economy principle as product architecture: costs are not a static dashboard, they are an operational investigation surface. Full accounting remains authoritative while expensive detail lists move to backend filters and offsets.
