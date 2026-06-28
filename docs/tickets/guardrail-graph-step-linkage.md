# Guardrail Graph Step Linkage

## Goal
Attach persisted guardrail results to the LangGraph step that made the routing/governance decision. Trace and Guardrails views should no longer treat post-run guardrail failures as only run-level events when the `route_review_or_finalize` graph step exists.

## Context
`GuardrailResult.graph_step_id` already existed and trace/catalog responses already exposed it, but post-run guardrail storage always wrote `None`. That weakened the traceability story: developers could see a guardrail failure, but not the exact workflow node responsible for the decision.

## Requirements
- Keep the existing database schema.
- Preserve current guardrail evaluation and policy behavior.
- Link stored guardrail results to the latest `route_review_or_finalize` step for the graph run.
- Keep fallback behavior safe if the step is missing.
- Add regression coverage for trace responses and guardrail catalog failures.

## Non-goals
- No new guardrail types.
- No guardrail policy changes.
- No frontend redesign.
- No migration or historical backfill.

## Implementation Notes
- Added optional `graph_step_id` to `GuardrailService.evaluate_and_store`.
- Added `AgentService._latest_step` to find the persisted routing step for a graph run.
- Passed the routing step id into guardrail persistence after graph completion.
- Added tests asserting trace guardrails and catalog recent failures expose graph step linkage.

## Verification
- `cd backend && uv run ruff check app/services/agent_service.py app/services/guardrails.py tests/test_agents.py tests/test_guardrails.py` passed.
- `cd backend && uv run pytest -s -q tests/test_guardrails.py tests/test_agents.py::test_support_agent_run_persists_trace_tool_calls_and_ai_runs` passed: 6 passed, 1 Starlette/httpx deprecation warning.
- `cd backend && uv run pytest -s -q tests/test_human_reviews.py tests/test_attention.py` passed: 10 passed, 1 Starlette/httpx deprecation warning.

## Human Review Checklist
- Confirm trace guardrail cards now link to the routing step through `graph_step_id`.
- Confirm guardrail policy behavior did not change.
- Confirm historical guardrail rows may still have null step ids; this ticket only affects new runs.
- Confirm this improves interview explanation: guardrail results are persisted, workspace-scoped, and linked to the LangGraph routing node.
