# Milestone 7: LangGraph Support-Agent Workflow

## What Was Built
Milestone 7 added the first LangGraph workflow:
- agent config creation/listing.
- support-agent graph runs.
- typed graph state.
- graph nodes for language detection, intent classification, retrieval, draft response, confidence scoring, routing, and finalization.
- persisted graph runs, graph steps, tool calls, and checkpoint placeholder table.
- trace endpoint with ordered steps and tool calls.
- linked `AIRun` records for mock model classification and draft response.

## Why Companies Care
Companies want AI workflows that can be debugged, audited, resumed, evaluated, and improved. LangGraph makes the control flow explicit: each node has a responsibility, state is inspectable, and conditional routing is testable. This is more credible than a black-box chatbot loop.

## How This Project Uses It
The support-agent graph retrieves cited evidence, drafts a same-language response with a mock model provider, scores confidence, and routes no-source cases to a human-review-needed status. Every important step is persisted for the future trace viewer.

## Design Tradeoffs
- The graph runs synchronously in local v1 so tests and demo behavior stay simple.
- Durable resume is postponed, but the checkpoint table and graph-run IDs prepare for it.
- Mock model calls are ledger-aware but not real AI quality evidence.
- Guardrails and actual human review resolution are intentionally left for Milestone 8.

## Failure Modes
- If graph nodes bypass service wrappers, traceability and token accounting break.
- If retrieval is not workspace-scoped, graph runs could leak evidence.
- If routing is too optimistic, unsupported answers may be finalized.
- If traces store too much raw text later, privacy risk increases.
- If the graph becomes too abstract, interviewers cannot understand or trust the workflow.

## Interview Explanation
“I used LangGraph to make the support workflow explicit and inspectable. Each node writes a graph step, retrieval writes a tool call and retrieval trace, and model-backed nodes write AI run ledger records. The graph is not an uncontrolled agent; it is a deterministic workflow with conditional routing. If retrieval finds no evidence, the run is marked as needing human review instead of generating an unsupported answer.”

## Review Checklist
- Verify every graph query filters by `workspace_id`.
- Verify every node creates a `GraphStep`.
- Verify retrieval creates a `ToolCall`.
- Verify classification/draft steps link to `AIRun`.
- Verify no-source cases do not finalize an answer.
