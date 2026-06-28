# Graph Trace Span Correlation

## Goal
Persist and expose trace/span identifiers for LangGraph runs so the trace viewer can identify the full run and each node execution with stable observability IDs.

## Context
The professional platform goal requires trace/span IDs when available. The app already stores `GraphRun`, `GraphStep`, AI runs, tool calls, guardrails, and checkpoints, but the trace viewer only showed database IDs indirectly.

## Requirements
- Add a stable `trace_id` to each graph run.
- Add `span_id` and `parent_span_id` to graph steps.
- Link each step to the previous persisted step for the current linear workflow.
- Expose IDs through the trace API.
- Show trace/span IDs in the frontend trace workbench.
- Add tests proving persistence and API ordering.

## Non-goals
- Do not implement full OpenTelemetry export.
- Do not redesign the trace viewer layout.
- Do not change LangGraph routing semantics.

## Implementation
- Added migration `0019_graph_trace_span_ids`.
- Added ORM fields on `GraphRun` and `GraphStep`.
- Added schema fields on `GraphRunResponse` and `GraphStepResponse`.
- Updated step persistence to attach the previous step span as the parent span.
- Updated the React trace workbench to show trace ID, span ID, and parent span ID.
- Updated support-agent trace tests to assert trace ID persistence and span chain integrity.

## Validation
- `cd backend && uv run ruff check app/models/agent.py app/schemas/agent.py app/services/support_agent_graph.py alembic/versions/0019_graph_trace_span_ids.py tests/test_agents.py` passed.
- `cd backend && uv run pytest -s -q tests/test_agents.py::test_support_agent_run_persists_trace_tool_calls_and_ai_runs` passed.
- `cd backend && uv run pytest -s -q tests/test_agents.py tests/test_human_reviews.py tests/test_attention.py` passed: 31 passed, 1 warning.
- `cd backend && uv run pytest -s -q` passed: 138 passed, 1 warning.
- `cd frontend && npm run build` passed.
- Browser QA was not rerun because WSL Playwright Chromium remains blocked by the missing `libnspr4.so` dependency and sudo requires a password.

## Human Review Checklist
- Confirm span IDs are visible in the trace workbench without crowding the main workflow.
- Confirm the parent span chain matches the current linear graph path.
- Confirm future branching/OpenTelemetry work is documented as non-goal, not silently implied as complete.

## Interview Notes
This ticket demonstrates the difference between storing a final answer and operating an AI workflow. Trace/span correlation lets engineers connect graph nodes, model calls, tools, guardrails, checkpoints, and future logs when debugging agent behavior.
