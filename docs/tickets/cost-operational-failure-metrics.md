# Cost Operational Failure Metrics

## Goal
Extend Usage & Costs beyond model spend so operators can see failed graph runs and failed tool calls alongside failed model calls.

## Context
The goal requires token/cost observability plus failed run count, tool error count, and model error count. The backend already returned model-call failures, latency percentiles, cache hit rate, and run/agent/model breakdowns. It did not expose graph-run failures or tool-call failures in the cost summary, so the cost dashboard could miss operational failures that were not model-provider errors.

## Implementation
- Added `failed_graph_runs` to the cost summary from persisted `GraphRun.status == failed`.
- Added `failed_tool_calls` to the cost summary from persisted failed `ToolCall` rows.
- Extended cost response schema and API mapping.
- Updated the frontend `CostSummary` type.
- Updated the Usage & Costs hero metrics to show failed model calls, failed graph runs, and tool errors separately.
- Updated cost posture copy so any operational failure category asks for review.
- Added regression coverage that inserts failed AI run, graph run, graph step, and tool call records and verifies all counts are workspace-scoped in the summary response.

## Validation
- `cd backend && uv run ruff check app/services/cost_service.py app/schemas/costs.py app/api/v1/costs.py tests/test_ai_observability.py`
- `cd backend && uv run pytest -s -q tests/test_ai_observability.py tests/test_budget_policies.py`
- `cd frontend && npm run build`
- `cd frontend && npm test -- --run`

## Results
- Ruff passed.
- Backend observability/budget tests passed: 12 passed, 1 existing Starlette/httpx warning.
- Frontend build passed.
- Frontend typecheck passed.

## Human Review Checklist
- Open Usage & Costs after a normal run and confirm failed counts are zero.
- Trigger or inspect a failed graph/tool/model case and confirm the dashboard separates model, graph, and tool failures.
- Confirm recent AI run ledger still shows provider/model/token/cost/cache details.
