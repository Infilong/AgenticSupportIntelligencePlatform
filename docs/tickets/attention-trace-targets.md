# Attention Trace Targets

## Goal
Make backend attention items open concrete trace evidence when the issue is tied to a graph run.

## Context
Overview and My Tasks now share the backend `/attention` queue. Some critical tasks, such as failed graph runs, failed model calls, and failed tool calls, had enough graph-run context to deep-link into Trace but still pointed at broad pages or lacked `target_id`.

## Requirements
- Failed graph run attention items should target the latest failed graph run trace.
- Failed model call attention items should target the related trace when `AIRun.graph_run_id` exists, otherwise keep the cost ledger target.
- Failed tool call attention items should target the related graph run trace.
- Preserve workspace scoping and existing attention item categories.
- Add tests proving trace target IDs are emitted.

## Non-goals
- Do not add a new attention API.
- Do not change frontend routing in this ticket.
- Do not alter review, guardrail, document, or evaluation task behavior.

## Implementation
- Updated `AttentionService` to load the latest failed `GraphRun`, `AIRun`, and `ToolCall` rows instead of only max timestamps.
- Added `target_id` for traceable failures.
- Updated action labels for traceable failures to `Inspect trace`.
- Added a regression test that creates failed graph, model, and tool records and asserts all three attention items point to the same graph run trace.

## Validation
- `cd backend && uv run ruff check app/services/attention_service.py tests/test_attention.py --fix` fixed import formatting.
- `cd backend && uv run ruff check app/services/attention_service.py tests/test_attention.py` passed.
- `cd backend && uv run pytest -s -q tests/test_attention.py` passed: 4 passed, 1 warning.
- `cd frontend && npm run build` passed.
- Browser QA was not rerun because WSL Playwright Chromium remains blocked by the missing `libnspr4.so` dependency and sudo requires a password.

## Human Review Checklist
- Confirm failed graph/model/tool tasks on Overview or My Tasks open Trace when a target id exists.
- Confirm model failures without graph context still open Costs.
- Confirm attention item sorting still prioritizes critical failures.

## Interview Notes
This ticket strengthens the operations-console story: attention tasks are not just labels, they route operators directly to the evidence needed to debug LangGraph, model, and tool failures.
