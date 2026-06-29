# Trace Run High-Cost Filter

## Goal
Make Runs / Traces useful for token-economy investigations, not only status debugging. Operators should be able to isolate expensive LangGraph executions directly from the trace run history.

## Context
The professional-platform audit still called out run-history filtering by failed, reviewed, and high-cost. Status filtering already covers failed and review-routed runs. This ticket adds high-cost filtering and ledger-derived cost metadata to the trace run list while keeping the trace detail endpoint unchanged.

## Requirements
- Keep `GET /agent-runs/{run_id}` and `/trace` stable.
- Enrich `GET /agent-runs` list rows with model call count, total tokens, estimated cost, and AI latency.
- Add `cost_view=high_cost` and `min_estimated_cost` query support.
- Compute cost metadata from persisted `AIRun` rows, not frontend heuristics.
- Keep workspace isolation and `traces:read` enforcement.
- Show cost/tokens/latency in the Trace page run history.

## Non-goals
- Do not change token accounting formulas.
- Do not mutate or delete graph runs or AI ledger rows.
- Do not redesign the full trace viewer.
- Do not add cost filtering to unrelated pages in this ticket.

## Design Summary
- Added `GraphRunListItemResponse` for list-only operational fields.
- `AgentService.list_graph_runs()` now returns aggregated list rows from `GraphRun` plus `AIRun` rollups.
- `AgentService.count_graph_runs()` counts the same grouped query, including high-cost filters.
- The Trace page added an `All costs / High cost` selector and threshold input.
- Trace list rows now show model calls, tokens, estimated cost, and latency when ledger data exists.

## Test Plan
- Extend the graph-run history test with three `AIRun` rows at different costs.
- Assert list rows include model calls, tokens, estimated cost, and latency.
- Assert `cost_view=high_cost` returns only the run above the threshold.
- Assert a different workspace still sees zero runs.
- Run backend agent tests, ruff, frontend typecheck/build, and diff checks.

## Acceptance Criteria
- Runs / Traces can isolate high-cost runs without using the Cost page first.
- High-cost filtering is backend-owned and workspace-scoped.
- The list remains bounded through limit/offset/total metadata.
- Existing trace detail APIs remain compatible.

## Human Review Checklist
- Confirm the high-cost threshold control is understandable in the Trace page.
- Confirm cost metadata is visible but not visually dominant over status/routing.
- Confirm the default run-history view still works for normal debugging.

## Interview Notes
- Explain why trace operations need high-cost filtering for production AI systems.
- Explain why cost rollups should come from the AI run ledger rather than frontend calculations.
- Explain why the list endpoint uses a separate response type from trace detail rows.
