# Agent Lifecycle Archive Controls

Date: 2026-06-28

## Goal
Add backend-supported lifecycle management for agents so the Agents page is not limited to create/configure/run. Owners need a safe way to remove obsolete agents from active operation without destroying graph runs, traces, AI run ledger records, or auditability.

## Context
The professional platform audit identified that agents lacked archive/delete lifecycle controls. A hard delete would cascade through `graph_runs` and erase trace history, which conflicts with the platform goal of explainable stateful AI agent operations. This ticket therefore implements owner-only soft deletion through an archive timestamp.

## Implementation
- Added `AgentConfig.archived_at` and Alembic migration `0011_agent_lifecycle`.
- Added `archived_at` to `AgentResponse`.
- Updated `AgentService.list_agents()` to hide archived agents by default and support `include_archived=true`.
- Added `AgentService.archive_agent()` to set `active=false` and `archived_at`.
- Updated `run_agent()` to reject inactive or archived agents with `409 agent_unavailable`.
- Added owner-only `DELETE /api/v1/workspaces/{workspace_id}/agents/{agent_id}` as a soft archive endpoint.
- Added `agent.archived` audit log recording.
- Added owner permission label `agents:delete`.
- Added frontend owner-only Archive agent control with a restricted permission note for non-owners.

## Backend/API Impact
- `GET /agents` returns only non-archived agents by default.
- `GET /agents?include_archived=true` returns active and archived agents.
- `DELETE /agents/{agent_id}` requires workspace owner permission and preserves historical traces.
- Running archived or inactive agents returns `409 agent_unavailable`.

## Validation
- `uv run ruff check .` passed.
- `uv run pytest tests/test_agents.py -q -s` passed: 15 tests.
- `uv run pytest -q -s` passed: 97 tests.
- `npm run test -- --run` passed.
- `npm run build` passed.

## Human Review Checklist
- Archive an agent from the Agents page as an owner and confirm it disappears from active selection.
- Confirm prior traces for that agent remain accessible.
- Confirm a member sees the owner-permission note and cannot archive agents.
- Confirm audit logs show `agent.archived`.

## Risks and Tradeoffs
- The endpoint uses `DELETE` semantics but performs a soft archive to protect operational evidence. This is intentional and should be explained as audit-preserving deletion.
- There is no archived-agent recovery UI yet. Recovery would require a separate owner-only restore endpoint.
- The active list does not yet provide an archived-agents management page.

## Interview Notes
This ticket is useful for discussing why production AI platforms preserve execution evidence. Deleting an agent configuration should not erase model-call ledgers, graph traces, or human-review history. The solution uses owner-only authorization, soft deletion, audit logging, and tests for workspace isolation.
