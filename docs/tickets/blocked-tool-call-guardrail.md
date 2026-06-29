# Blocked Tool Call Guardrail

## Goal
Make disabled or blocked tool execution visible as governance evidence, not only as a failed tool-call row.

## Context
The platform already records failed `ToolCall` rows when `search_documents` is disabled by workspace configuration. However, the Guardrails page and trace guardrail evidence did not have a dedicated policy result for blocked tool execution. The product goal requires unsafe tool-call blocking and permission/tool governance to be first-class.

## Requirements
- Add a catalog guardrail for blocked unsafe tool calls.
- Record a failed guardrail decision when a disabled tool is encountered during LangGraph execution.
- Include the guardrail in route reasons so human-review routing is explainable.
- Preserve existing failed `ToolCall` trace evidence.
- Keep this fixed policy non-configurable in v1.

## Non-goals
- Do not add arbitrary external tools.
- Do not implement a full tool permission policy engine in this ticket.
- Do not change the existing tool enable/disable API.
- Do not change retrieval behavior when the tool is enabled.

## Design Plan
- Add `unsafe_tool_call` to the runtime guardrail catalog.
- Extend guardrail evaluation to fail when `SupportAgentState.tool_disabled` is set.
- Add `unsafe_tool_call` to route reason checks.
- Add typed state support for `tool_disabled`.
- Extend the disabled retrieval tool test to assert route, trace, and catalog evidence.

## Files Changed
- `backend/app/services/guardrail_catalog_service.py`
- `backend/app/services/guardrails.py`
- `backend/app/services/support_agent_graph.py`
- `backend/app/services/support_agent_state.py`
- `backend/tests/test_tools.py`
- `docs/tickets/blocked-tool-call-guardrail.md`

## Test Plan
- `cd backend && uv run pytest -s -q tests/test_tools.py tests/test_guardrails.py`
- `cd backend && uv run ruff check app/services/guardrail_catalog_service.py app/services/guardrails.py app/services/support_agent_graph.py app/services/support_agent_state.py tests/test_tools.py`

## Acceptance Criteria
- Disabled `search_documents` still records a failed `ToolCall`.
- Disabled `search_documents` adds `unsafe_tool_call` to route reasons.
- Trace guardrails include failed `unsafe_tool_call` evidence.
- Guardrail catalog shows the blocked tool failure with recent trace link data.

## Risks
- The name `unsafe_tool_call` currently covers disabled-tool blocking; future external action tools may need more granular guardrail types.
- Fixed policy is appropriate for v1, but larger deployments may need per-tool allowlists and role-aware tool policy rules.

## Human Review Checklist
- Disable `search_documents`, run an agent, and inspect the trace guardrail section.
- Confirm the Tools page still shows the failed execution row.
- Confirm the Guardrails page shows Tool call blocked with a recent failure.
- Confirm enabled retrieval still succeeds normally.

## Interview Notes
This is a platform maturity detail: if tool execution is blocked by governance, it should be visible as a guardrail result and a trace reason, not just as a low-level exception or failed call.
