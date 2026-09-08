# LangGraph Workflow Design

## Numeric duration support
The default unsupported-answer policy routes a draft to review when a numeric duration is absent
from the nonempty packed source text it actually cites. `answer_duration_support.py` normalizes
full-width digits, decimal formatting and supported EN/JA/ZH unit aliases; business days remain
distinct from calendar days. Citation titles and uncited chunks cannot supply supporting values.
The shared check runs at routing and final guardrail publication, without extra model calls.
Existing policy enable/action settings remain effective; human reviewers retain publication authority.

This is a conservative quantity check, not factual entailment. Matching values can describe
different policies or relations; negation, word-number quantities, general dates/ranges, currency
and other claims remain unverified. Unit conversions may require review. See the
[verification plan](exec-plans/completed/answer-duration-support.md) for evidence and remaining scope.

## Goal
Use LangGraph for the main support-agent workflow. The workflow should be stateful, inspectable, and testable. Do not build an uncontrolled autonomous agent.

## Mock response contract
`backend/app/services/mock_support_answer.py` owns deterministic mock response text. It quotes
the first nonempty citable packed source, up to 800 characters with an explicit truncation mark,
and includes the source citation. EN/JA/ZH labels identify simulation and avoid claiming a policy
decision. Intent or user wording cannot invent exceptions or policy facts. Missing citable
evidence returns a localized review message. Real providers still receive the configured prompt;
this helper supplies only mock completion text and planning estimates. An excerpt is not proof
of question relevance, policy applicability or factual entailment. See [verification](testing.md#multilingual-policy-repair-verification).

## Answer citation boundary
`answer_citations.py` checks the generated draft for an exact reference from a nonempty chunk
actually packed into model context. `graph_routing.py` and persisted publication guardrails
use the same check. Retrieved-but-trimmed sources and a metadata-only citation list cannot
satisfy it. With the default citation policy, an uncited draft routes to review, remains a
review proposal and never becomes the final answer. Provider usage and graph traces remain
available. Existing operator disabled/record-only policy overrides retain their semantics.

Every canonical `#chunk-` marker must be consumed by an exact citation from nonempty packed
evidence. Unknown, malformed or version/index-altered references cannot hide beside a valid one;
repeated valid references are allowed. Remaining markers conservatively route to review, including
literal examples of this syntax in source prose. This is citation integrity, not factual entailment:
an answer can still contain unsupported claims or invented references expressed in other syntax.
Semantic relevance,
claim-level support and robust refusal detection remain required AI-quality work. Providers
must preserve the supplied exact citation string; shortened/paraphrased references fail this check.

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
- Classification and draft prompts are built with LangChain Core `ChatPromptTemplate`; retrieved chunks are wrapped as LangChain `Document` objects before prompt assembly; output text passes through LangChain `StrOutputParser`.
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

## Human answer reference validation
Approval and edit validate the selected answer before mutating review/run state. Blank answers
are rejected. Answers containing canonical `#chunk-` references must match nonempty evidence
from the latest successful `compress_context` step for this workspace and run; if the latest
step failed, evidence is not accepted. Missing/malformed evidence or mixed invented references
return `human_review_invalid_decision` (400), leaving the review pending for correction.
The original packed snapshot is used, not today's document version. This proves reference
integrity, not factual support or current-policy validity. Legacy cited drafts without that
snapshot must be edited or rejected. Uncited human-authored safe responses remain allowed;
human judgment can resolve cases the model could not answer. Rejection needs no evidence.
The existing locked, atomic review/run/checkpoint/audit transition remains the publication owner.
