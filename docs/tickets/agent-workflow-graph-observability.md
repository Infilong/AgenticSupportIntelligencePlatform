# Agent Workflow Graph Observability

Date: 2026-06-28

## Goal
Make the Agents page show the actual LangGraph support-agent harness as a backend-supported workflow graph, not a hardcoded frontend list. Developers should see nodes, edges, conditional routing, persistence, LangChain components, and real per-node execution signals for the selected agent.

## Context
The platform objective requires stateful workflow concepts to be first-class: graph nodes, edges, graph state, checkpoints, conditional routing, retries, human-review routing, failure states, and finalization states. The trace endpoint already enriches executed steps, but the Agent page currently shows a static seven-node list. That weakens the professional AI platform story.

## Requirements
- Add a workspace-scoped `GET /api/v1/workspaces/{workspace_id}/agents/{agent_id}/workflow` endpoint.
- Validate the agent belongs to the current workspace.
- Return workflow metadata from backend code, including nodes, edges, conditional routes, persistence stores, and LangChain components.
- Aggregate per-node stats from persisted `GraphStep` records for the selected agent.
- Include recent failures for node debugging.
- Add backend tests for workflow metadata, step stats, failure signals, and workspace isolation.
- Replace the static Agent page node list with the new workflow summary.
- Keep graph editing out of scope; this is an observability and harness-inspection surface.

## Non-goals
- Do not add a graphical canvas editor.
- Do not make the workflow dynamically configurable.
- Do not change LangGraph execution semantics.
- Do not add database tables or migrations.

## Design Plan
Backend:
- Add workflow response schemas in `app.schemas.agent`.
- Add `AgentService.get_workflow_summary()` using static runtime metadata plus `GraphStep` aggregates scoped by `agent_config_id`.
- Add route `GET /workspaces/{workspace_id}/agents/{agent_id}/workflow`.
- Reuse existing `_node_role()` and LangChain runtime component semantics where practical.

Frontend:
- Add `AgentWorkflowSummary` types and state.
- Load workflow summary when selecting/loading an agent.
- Replace the static harness list with a workflow graph card showing node order, roles, stats, conditional routes, and failure links.

## Test Plan
- Focused backend tests in `backend/tests/test_agents.py`.
- Frontend TypeScript and build checks.
- Full backend suite before commit.

## Acceptance Criteria
- Agent workflow endpoint returns all expected nodes and edges.
- Per-node run counts update after agent runs.
- A failed node appears in recent failure metadata.
- A user cannot inspect another workspace agent workflow.
- Agent UI uses backend workflow data instead of hardcoded node names.

## Human Review Checklist
- Confirm the Agent page makes the LangGraph harness obvious before running a trace.
- Confirm node stats are real after running the agent.
- Confirm conditional human-review routing is visually clear.
- Confirm the UI does not imply workflow editing exists yet.

## Interview Notes
This ticket is useful to explain the difference between an autonomous chatbot and a stateful AI workflow platform: the graph topology is visible, execution records are persisted per node, and debugging starts from workflow structure before drilling into traces.
