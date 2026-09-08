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

Rebuild internal actions use explicit `set_category` and `add_note` inputs. Agent
`allowed_actions` defaults to no mutation capabilities. Proposals bind workspace, run,
task and canonical inputs into a hash; approval must submit that hash. The service
rechecks both snapshotted and current agent capability and initiating-user authority.
Proposal outcome, note/category write and audit are one transaction. Notes have a unique
proposal reference. Rejection writes no task update. Stop serializes on the run lock;
retries may read a previously applied result but cannot create another side effect.
The worker stages category and draft-note proposals only after guardrails permit publication.
Inputs reuse accounted classifier/draft results; no additional model call is introduced.
Action endpoints inspect proposals and resolve exact hashes. Applied results record a
step/tool call atomically; answer publication waits for action resolution. Rejecting an
answer or stopping rejects pending actions. The new Work review form exposes these decisions;
Agents enables capabilities and the shared run record shows results. Deployed on revision 0035.
LangChain tools can wrap backend functions, but backend services own permissions, persistence, and auditability.

## Tests
Test successful calls, invalid input, permission denial, workspace leakage attempts, unsafe calls, and tool failure visibility.
