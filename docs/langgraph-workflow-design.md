# LangGraph Workflow Design

## Goal
Use LangGraph for the main support-agent workflow. The workflow should be stateful, inspectable, and testable. Do not build an uncontrolled autonomous agent.

## Graph Nodes
```text
detect_language
classify_intent
retrieve_evidence
compress_context
draft_response
check_policy_and_tone
score_confidence
route_review_or_finalize
finalize_response
```

## Graph State
```text
SupportAgentState
- workspace_id
- user_id
- input_message
- detected_language
- intent
- sentiment
- product_area
- safety_risk
- escalation_needed
- retrieved_chunks
- compressed_context
- draft_answer
- policy_check_result
- tone_check_result
- confidence_score
- token_budget
- estimated_cost
- route_decision
- final_answer
- citations
- errors
```

## Conditional Routing
Route to human review when:
- confidence is below threshold
- citation coverage is insufficient
- answer is unsupported
- output or request is unsafe
- token cost exceeds budget
- safety risk is high
- escalation is needed
- language-specific quality check fails
- prompt injection or unsafe request is detected

## Traceability
Every node execution creates a `GraphStep`. Every model call inside a node creates an `AIRun`. Every retrieval call creates a `RetrievalTrace`. Tool calls create `ToolCall` rows.

## Checkpointing
Workflow state should be checkpointable so human-review workflows can pause and resume. Checkpoints must be workspace-scoped.

## Testing
Tests should cover normal finalization, no-source refusal, low-confidence review routing, high-risk review routing, prompt-injection blocking, token-budget routing, failed node handling, and checkpoint/resume behavior.


## Implemented In Milestone 7
- Added LangGraph `StateGraph` workflow with typed `SupportAgentState`.
- Implemented nodes: `detect_language`, `classify_intent`, `retrieve_evidence`, `draft_response`, `score_confidence`, `route_review_or_finalize`, and `finalize_response`.
- Added `AgentConfig`, `GraphRun`, `GraphStep`, `ToolCall`, and `Checkpoint` tables.
- Every node persists a `GraphStep`.
- Retrieval is stored as a `ToolCall` and also creates a `RetrievalTrace` through the retrieval service.
- Classification and draft nodes call `MockModelProvider`, creating linked `AIRun` records.
- Trace endpoint returns ordered graph steps and tool calls.
- No-source cases route to `needs_human_review`; real human review API is Milestone 8.

Known limitations:
- Execution is synchronous for local v1.
- Checkpoint table exists, but durable resume is not implemented yet.
- Mock model responses are deterministic and not real AI quality evidence.
- Guardrails, prompt injection checks, and human review resolution are Milestone 8.


## Implemented In Milestone 8
- Completed graph runs are evaluated by deterministic guardrails.
- Blocking guardrail failures override finalize decisions and route to `needs_human_review`.
- No-source and prompt-injection cases create pending `HumanReview` records.
