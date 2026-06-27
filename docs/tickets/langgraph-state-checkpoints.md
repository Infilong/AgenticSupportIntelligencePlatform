# LangGraph State Checkpoints

## Goal
Make the support-agent runtime visibly stateful so engineers can inspect how LangGraph state changes after every node.

## Audit Finding
The project used LangGraph `StateGraph` and persisted `GraphStep` rows, but the existing `Checkpoint` table was only a placeholder. That made the app less convincing as a stateful AI operations platform because Trace Explorer showed step input/output but not durable state snapshots across the workflow.

## Changes Made
- Persisted a compact `Checkpoint` after every LangGraph node execution.
- Added checkpoint snapshots to the trace API response.
- Added checkpoint test coverage proving each graph node writes a checkpoint and that snapshots avoid raw retrieved chunks.
- Added a Trace Explorer `State checkpoints` section with snapshot count, latest state summary, and expandable checkpoint state cards.
- Kept raw long retrieved chunks out of checkpoint snapshots to preserve token economy and readability.

## Verification
- `uv run pytest -s tests/test_agents.py::test_support_agent_run_persists_trace_tool_calls_and_ai_runs` -> passed
- `uv run ruff check .` -> passed
- `uv run pytest -s` -> 85 passed
- `npm run test` -> passed
- `npm run build` -> passed
- `docker compose up -d --build api frontend` -> rebuilt and restarted
- Live API smoke -> 7 graph steps, 7 checkpoints, latest checkpoint `finalize_response`, raw retrieved chunks excluded
- `curl -I http://127.0.0.1:5173` -> 200 OK

## Current Scope
This is app-level durable checkpoint visibility around LangGraph node execution. It does not yet implement arbitrary pause/resume through a LangGraph-native checkpointer.

## Remaining Risks
- Checkpoints are compact JSON snapshots, not a complete replay/event-sourcing mechanism.
- Full human-review resume semantics should be a later ticket: approve/edit/reject should create explicit resumed/finalized state transitions.
- The trace UI is still in a large single React file and should eventually be split into components.

## Next Recommended Ticket
Add human-review resume semantics: when a reviewer approves or edits an answer, persist a post-review finalization checkpoint and audit event that connects the human decision back to the original graph run state.
