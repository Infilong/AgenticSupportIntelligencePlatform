# Agent Configuration Control Center

## Goal
Make the Agent page feel like a professional AI platform control surface instead of a mixed create/run form. Users should understand which agent is selected, what workspace and role they are operating under, how token/retrieval/model controls affect the workflow, and where to inspect model cost or traces.

## Context
The backend already exposes real agent lifecycle and operational data:
- `POST /agents` creates a workspace-scoped agent.
- `PATCH /agents/{id}` updates name, token budget, confidence threshold, retrieval settings, and model route.
- `GET /agents/{id}/summary` returns run/cost/latency history.
- `GET /agents/{id}/workflow` returns the backend-defined LangGraph/LangChain harness summary.

The previous frontend had runtime controls, but they were placed below the run console, making configuration feel secondary.

## Requirements
- Move runtime controls into a first-class configuration control center near the top of the Agent page.
- Use the existing backend `PATCH /agents/{id}` path; do not create display-only controls.
- Show selected agent identity, workspace, role, token budget, confidence threshold, retrieval top K/min score, and model route.
- Keep run history, workflow graph, and run console visible below.
- Keep archiving owner-gated.
- Add browser coverage that the control center is visible, editable, and saves through the real API.

## Non-goals
- No backend schema changes.
- No new agent permission model in this ticket. Backend currently allows workspace members to update/run agents while archiving remains owner-only.
- No prompt editing or tool editing changes.

## Implementation Notes
- Added an `agent-control-center` section directly after readiness cards.
- Reused `updateAgentRuntime` for the save action.
- Moved the persisted settings readout into the control center.
- Removed the duplicate bottom runtime panel.
- Added CSS for grouped identity, token economy, retrieval, model route, lifecycle, and persisted setting cards.
- Split new-agent naming state from selected-agent configuration state so creating an agent and editing the selected agent no longer share one input value.

## Verification
- `cd frontend && npm test -- --run` - typecheck passed.
- `cd frontend && npm run build` - production build passed.
- `docker compose up -d --build frontend` - rebuilt the local browser target.
- `make frontend-e2e-docker` - 1 Playwright smoke test passed, including Agent control-center edit/save, dataset example search, knowledge chunk search, review, and trace entry points.

## Human Review Checklist
- Confirm the Agent page now makes selected agent configuration obvious before running.
- Confirm controls are not fake and save through the existing API.
- Confirm the page remains readable on narrow screens.
- Confirm owner-only archive messaging is still clear.
