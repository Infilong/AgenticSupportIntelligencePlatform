# Milestone 7: LangGraph Support-Agent Workflow

## Goal
Build the first inspectable LangGraph support-agent workflow over the existing platform foundation.

The workflow should detect language, classify intent, retrieve evidence, draft a same-language response with the mock model provider, score confidence, route to finalize or human-review-needed status, and persist trace data for every graph node.

## Context
Implemented foundation:
- workspace auth and permissions.
- multilingual datasets and knowledge docs.
- retrieval with citations and retrieval traces.
- AI run ledger, mock model provider, token budget planner, cost summary.

Current LangGraph docs checked via Context7:
- use `StateGraph` with TypedDict state.
- use `START` and `END` constants from `langgraph.graph`.
- add nodes with `add_node`.
- connect nodes with `add_edge`.
- conditional routing uses `add_conditional_edges(source, path, path_map)`.
- compile with `graph.compile()`; checkpointer can be added later.

## Requirements
- Add LangGraph/LangChain dependencies with uv.
- Add SQLAlchemy models and migration for:
  - `AgentConfig`
  - `GraphRun`
  - `GraphStep`
  - `ToolCall`
  - `Checkpoint`
- Add typed graph state `SupportAgentState`.
- Add graph nodes:
  - `detect_language`
  - `classify_intent`
  - `retrieve_evidence`
  - `draft_response`
  - `score_confidence`
  - `route_review_or_finalize`
  - `finalize_response`
- Persist a `GraphStep` for every node execution.
- Persist `ToolCall` for retrieval tool usage.
- Link model-call graph steps to `AIRun` where a mock model call is used.
- Add API routes:
  - `POST /api/v1/workspaces/{workspace_id}/agents`
  - `GET /api/v1/workspaces/{workspace_id}/agents`
  - `POST /api/v1/workspaces/{workspace_id}/agents/{agent_id}/runs`
  - `GET /api/v1/workspaces/{workspace_id}/agent-runs/{run_id}`
  - `GET /api/v1/workspaces/{workspace_id}/agent-runs/{run_id}/trace`
- Enforce workspace isolation for agents and graph runs.
- Add tests for successful graph run, trace persistence, same-language draft behavior, AI run linkage, tool call persistence, no-source route, and cross-workspace denial.

## Non-goals
- No uncontrolled autonomous agent.
- No real LLM provider.
- No human review model/API yet; Milestone 8 owns that.
- No frontend trace viewer yet; Milestone 10 owns UI.
- No advanced checkpoint/resume beyond a `Checkpoint` table placeholder.
- No prompt template management UI.

## Design Plan
- Add dependencies: `langgraph`, `langchain-core` if required.
- Add `backend/app/models/agent.py`.
- Add `backend/app/schemas/agent.py`.
- Add `backend/app/services/support_agent_state.py`.
- Add `backend/app/services/support_agent_graph.py`.
- Add `backend/app/services/agent_service.py`.
- Add `backend/app/api/v1/agents.py` and include in v1 router.
- Add migration `0006_agent_workflow.py`.
- Update docs and learning notes.

## Database Migrations
Create:
```text
AgentConfig
- id
- workspace_id
- name
- active
- model_config_id nullable
- token_budget
- settings_json
- created_at

GraphRun
- id
- workspace_id
- agent_config_id
- user_id
- input_message
- language nullable
- status
- route_decision nullable
- final_answer nullable
- created_at
- completed_at nullable

GraphStep
- id
- workspace_id
- graph_run_id
- step_name
- input_json
- output_json
- status
- latency_ms
- ai_run_id nullable
- token_count nullable
- estimated_cost nullable
- error_message nullable
- retry_count
- created_at

ToolCall
- id
- workspace_id
- graph_run_id
- graph_step_id
- tool_name
- input_json
- output_json
- status
- latency_ms
- created_at

Checkpoint
- id
- workspace_id
- graph_run_id
- checkpoint_key
- state_json
- created_at
```

## API Changes
Run request:
```json
{
  "input_message": "返金は何日以内ですか？"
}
```

Run response includes run ID, status, route decision, language, final answer, citations, and summary costs.

Trace response includes graph run, ordered steps, tool calls, and linked AI run IDs/cost fields.

## Test Plan
- create agent config and run support agent over indexed refund document.
- assert every graph node stores a `GraphStep`.
- assert retrieval stores a `ToolCall` and retrieval trace exists.
- assert draft step links to `AIRun`.
- assert Japanese input receives Japanese mock response text.
- assert no-source query routes to `human_review` or no-source status.
- assert another workspace cannot read run/trace.

## Risks
- LangGraph integration can become too abstract. Keep graph nodes explicit and traceable.
- Mock responses can look fake if not clearly documented; use deterministic mock behavior only for tests/local v1.
- Broad exception handling could hide graph-node failures. Persist failed steps and re-raise controlled errors.
- Workflow scope can expand into guardrails/human review; leave that for Milestone 8.

## Acceptance Criteria
- graph run stores every step.
- workflow detects language.
- workflow retrieves evidence.
- workflow drafts same-language response.
- workflow stores tool calls.
- workflow stores AI runs.
- trace endpoint returns full graph execution.
- tests cover graph routing and failures.
- validation passes and commit is pushed.

## Human Review Checklist
- Confirm the graph is inspectable, not autonomous magic.
- Verify graph steps are understandable in API responses.
- Verify workspace filters exist on every graph query.
- Verify AI run linkage is real.
- Verify no-source routing is conservative.

## Interview Notes
Be able to explain:
- why LangGraph is used for workflow orchestration rather than hidden agent behavior.
- how graph traces support debugging and compliance.
- how retrieval/tool calls and AI runs attach to graph steps.
- how token/cost accounting is preserved inside workflow execution.
- why human review routing is a conditional workflow decision.


## Implementation Record
Completed implementation details:
- Added LangGraph and LangChain Core dependencies with uv.
- Added `backend/app/models/agent.py` and migration `0006_agent_workflow.py`.
- Added `SupportAgentState`, `SupportAgentGraphRunner`, and `AgentService`.
- Added agent APIs for create/list/run/get run/get trace.
- Added `backend/tests/test_agents.py`.
- Updated architecture, API, LangGraph, observability, learning, and ticket docs.

Important decisions:
- Use synchronous graph execution for local v1.
- Use explicit LangGraph nodes rather than an autonomous loop.
- Persist `GraphStep` for every node.
- Persist retrieval as `ToolCall` and model calls as linked `AIRun` records.
- Route no-source cases to `needs_human_review`; full human review workflow remains Milestone 8.

Validation results:
- `make backend-lint`: passed.
- `make backend-test`: 45 passed, 1 existing TestClient deprecation warning.
- `make backend-migrate`: passed against Docker PostgreSQL/pgvector.
- Docker API smoke: uploaded knowledge doc, created agent, ran graph, fetched trace, verified tool call and AI run linkage.

Self-review result:
- No unresolved P0/P1 issues found.
- P2: graph execution is synchronous; async worker execution is still future work.
- P2: checkpoint table exists but resume/checkpoint behavior is not implemented.
- P2: mock answer quality is deterministic and not real model behavior.
- P2: full guardrails and human review resolution are intentionally deferred to Milestone 8.
