# Cost and Performance Observability Upgrade

## Goal
Make token economy and model-performance observability more professional by connecting cost data to agents, graph runs, recent AI ledger rows, latency percentiles, cache behavior, and failed model calls.

## Context
The active product objective requires token/cost dashboards by workspace, agent, model, and run; latency P50/P95/P99; cache hit rate; failed model counts; and traceability from cost spikes back to graph runs. Before this ticket, the cost summary exposed workspace totals plus purpose/model grouping, average latency, and cache hit rate only.

## Requirements
- Keep cost data workspace-scoped through backend authorization.
- Extend the existing cost summary API instead of adding fake frontend-only metrics.
- Add latency P50/P95/P99 from real AI run ledger rows.
- Add failed AI run count.
- Add cost/token/latency breakdown by agent.
- Add recent graph-run cost rows with trace links in the UI.
- Add recent AI run ledger rows showing provider, model, purpose, token split, cache state, status, latency, and errors.
- Add tests proving the new payload is backed by real graph runs and failed AI runs.

## Backend Changes
- Extended `CostService.summarize_workspace()` with:
  - `latency_p50_ms`
  - `latency_p95_ms`
  - `latency_p99_ms`
  - `failed_ai_runs`
  - `by_agent`
  - `recent_runs`
  - `recent_ai_runs`
- Added public response schemas for agent, graph-run, and AI-ledger cost summaries.
- Updated `/api/v1/workspaces/{workspace_id}/costs/summary` mapping.
- Added tests for real agent-run cost attribution and failed model call counting.

## Frontend Changes
- Upgraded Usage & Costs from aggregate cards into an operations console.
- Added latency percentile cards and failed AI call visibility.
- Added Cost by Agent cards.
- Added Recent graph-run spend with direct Trace page links.
- Added Recent AI run ledger rows with status, token split, cost, latency, cache state, and error messages.
- Preserved existing purpose/model breakdowns.

## Verification
- `cd backend && uv run ruff check app tests/test_ai_observability.py`
- `cd backend && uv run pytest tests/test_ai_observability.py -q -s`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm run build`

## Human Review Checklist
- Run an agent and open Usage & Costs.
- Confirm by-agent and recent graph-run sections appear.
- Click a recent graph-run cost row and confirm it opens the Trace page for that run.
- Trigger or inspect a failed model call and confirm the failed count and ledger row are visible.
- Confirm the dashboard does not claim real spend if only mock model providers are being used.

## Known Limitations
- Percentiles are computed in Python from the current workspace AI run set; this is fine for local-team scale but should move to database/window functions or a metrics store at larger scale.
- Recent run and AI ledger lists are capped at 20 rows.
- This remains estimated cost from model config pricing, not provider billing reconciliation.
