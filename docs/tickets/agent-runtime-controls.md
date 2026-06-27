# Agent Runtime Controls

## Goal
Move the support agent from fixed demo behavior toward a professional admin/developer tool by making key graph behavior configurable per workspace agent.

## Context
The app already exposed model and prompt settings, but agent behavior still used hardcoded retrieval and routing thresholds. A serious AI platform should let technical operators tune the workflow harness without editing code.

## Changes
- Added `PATCH /api/v1/workspaces/{workspace_id}/agents/{agent_id}`.
- Added editable agent runtime settings:
  - `token_budget`
  - `confidence_threshold`
  - `retrieval_top_k`
  - `retrieval_min_score`
- Stored runtime settings in `AgentConfig.settings_json`.
- Passed settings into `SupportAgentState` for LangGraph execution.
- Retrieval node now uses agent `retrieval_top_k` and `retrieval_min_score`.
- Routing node now uses agent `confidence_threshold`.
- Graph trace now records route reasons and confidence threshold.
- Human review reason now includes graph route reasons, not only guardrail failures.
- Frontend agent page now includes a Runtime controls panel for developers/admins.

## Tests
- Agent settings can be updated through a workspace-scoped API.
- Cross-workspace agent update returns 404.
- Strict confidence threshold changes a normally finalized refund answer into human review.
- Retrieval tool trace records configured `top_k` and `min_score`.
- Route step trace records configured confidence threshold.

## Verification
- `uv run ruff check .`
- `uv run pytest -s`
- `npm run test`
- `npm run build`

## Risks
- Settings are stored as JSON for speed in this portfolio version. A larger production version may move each setting into typed columns with audit history.
- The settings set is intentionally small. More knobs are possible, but too many options would make the UI less intuitive.

## Interview Notes
Explain this as the agent harness layer: model choice, prompts, retrieval, and routing are separately configurable. The graph remains deterministic and inspectable, but operators can tune risk tolerance and retrieval behavior per workspace agent.
