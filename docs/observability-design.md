# Observability Design

## Goal
Make AI workflow behavior inspectable. The system should show what happened, why it happened, which data was used, how much it cost, and whether quality passed.

## Required Records
- `GraphRun` for full workflow execution
- `GraphStep` for each LangGraph node
- `ToolCall` for tool execution
- `AIRun` for every model call
- `RetrievalTrace` and `RetrievedChunk` for retrieval
- `GuardrailResult` for guardrails
- `EvaluationRun`, `EvaluationResult`, and `EvaluationMetric` for evaluation
- `AuditLog` for workspace actions

## Required Frontend Pages
```text
/login
/workspaces
/workspaces/{id}/datasets
/workspaces/{id}/documents
/workspaces/{id}/agent
/workspaces/{id}/agent-runs/{run_id}/trace
/workspaces/{id}/evaluations
/workspaces/{id}/costs
/workspaces/{id}/audit-logs
/settings
```

## Graph Run Trace Viewer
Show input message, detected language, intent classification, retrieved chunks, retrieval scores, selected citations, compressed context summary, draft response, policy/tone check, confidence score, routing decision, human-review status, final answer, model calls, token usage, estimated cost, latency, errors, and retries.

## Evaluation Dashboard
Show metrics by English, Japanese, and Chinese: groundedness pass rate, citation accuracy, average cost, average latency, human-review rate, and language preservation pass rate. Also show baseline comparison: Direct LLM vs Vector RAG vs Hybrid RAG + Compression + Guardrails.

## Cost Dashboard
Show token usage, estimated cost, latency, model choice, cache hit rate, purpose, language, and trend summaries by workspace.


## Implemented In Milestone 6
- `AIRun` persistence for mock model calls.
- Workspace-scoped cost summary API.
- Token, estimated cost, latency, cache hit, status, and purpose tracking.
- Failed model calls are also recorded with error messages.
