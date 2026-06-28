# Agent Operational Summary Management

Date: 2026-06-28

## Goal
Make the Agents page feel like a professional AI operations surface instead of only a run form. The page should show real backend-supported run history, review/failure counts, token usage, estimated cost, and latency for the selected agent.

## Context
The professional platform audit identified that agent management lacked recent runs, failure rate, cost/latency summary, and direct trace entry points. Existing backend data already records `GraphRun`, `GraphStep`, `AIRun`, tool calls, guardrails, and checkpoints, but there was no per-agent management summary API.

## Implementation
- Added `AgentOperationalSummaryResponse` to the agent schemas.
- Added `AgentService.get_operational_summary()` to aggregate per-agent operational data from real `GraphRun` and `AIRun` records.
- Added `GET /api/v1/workspaces/{workspace_id}/agents/{agent_id}/summary`.
- Added backend tests proving summary aggregation and workspace isolation.
- Added frontend `AgentOperationalSummary` state and loading for selected agents.
- Redesigned the Agents page around:
  - operations metrics
  - recent run trace entry points
  - visible LangGraph harness path
  - runtime control readout
  - existing run console and latest outcome panel

## Backend Contract
The summary endpoint returns:
- selected agent metadata
- recent runs, newest first
- total run count
- completed run count
- human-review run count
- failed run count
- total tokens from AI run ledger records
- total estimated cost from AI run ledger records
- average AI latency from AI run ledger records
- last run timestamp

The endpoint uses workspace-scoped agent lookup. If a user requests an agent from another workspace, the API returns `404 agent_not_found`.

## Validation
- `uv run ruff check .` passed.
- `uv run pytest tests/test_agents.py -q -s` passed: 13 tests.
- `uv run pytest -q -s` passed: 95 tests.
- `npm run test -- --run` passed.
- `npm run build` passed.

## Human Review Notes
Review the Agents page with several runs in the same workspace. Confirm that the recent-run rows open the correct trace, summary metrics update after new runs, and the graph harness does not imply configurable tool/guardrail registries that do not exist yet.

## Known Limitations
- Agent tools and guardrails are still runtime-visible, not first-class configurable resources.
- The summary uses average AI-call latency, not P50/P95/P99 run latency.
- The endpoint currently returns the latest 8 runs without pagination.
- There is no agent archive/delete lifecycle yet.

## Interview Notes
This ticket is useful to explain how a backend-owned operational summary avoids fake frontend status. It connects LangGraph run records, AI run ledger cost tracking, and workspace isolation into a product surface that helps engineers debug and operate agents.
