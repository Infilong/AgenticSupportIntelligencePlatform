# Tool Execution Design

## Goal
Tool execution should be explicit, permission-checked, traceable, and testable. Tools are not a way to bypass backend architecture.

## Initial Tools
- `search_documents`
- `get_document_chunk`
- `compare_policy`
- `draft_response`
- `calculate_cost`

## Rules
- Every tool call is workspace-scoped.
- Every tool call creates a `ToolCall` record.
- Tools must validate inputs with structured schemas.
- Tools must not access data outside the current workspace.
- Unsafe tool calls must be blocked and logged through guardrails.
- Tool failures should be explicit and visible in graph trace data.

## LangChain Boundary
LangChain tools can wrap backend functions, but backend services own permissions, persistence, and auditability.

## Tests
Test successful calls, invalid input, permission denial, workspace leakage attempts, unsafe calls, and tool failure visibility.
