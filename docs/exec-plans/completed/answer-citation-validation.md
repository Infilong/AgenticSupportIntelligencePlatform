# Answer citation validation
## Goal
Prevent uncited provider answers from being finalized merely because retrieval found evidence.
## Context
Citation guardrails currently inspect retrieval metadata rather than the generated answer.
## Requirements
Routing and publication require an exact citation from nonempty packed evidence in the answer.
Preserve configurable guardrail policy, model accounting, review proposal and trace evidence.
## Non-goals
Factual entailment grading, semantic retrieval, changing provider credentials or paid calls.
## Acceptance Criteria
Uncited/empty/invented-reference answers fail citation validation; EN/JA/ZH uncited provider
responses route to review with two recorded calls and no final answer. Valid mock journeys pass.
## Plan
1. Reproduce via pure guardrail and provider-boundary regressions.
2. Add a small shared citation helper; extract routing rules from the oversized graph.
3. Run affected/full tests, lint and live journeys; record evidence and remaining AI-quality gaps.
## Verification
Retain before/after logs under `.artifacts/20260907-answer-citations/`. Tests use mock transport
and real ledger/graph/review persistence. No paid API requests.
## Risks
Exact reference matching requires providers to preserve supplied citation strings. Presence
does not prove factual support. Existing operator policy overrides remain explicit behavior.
## Progress
2026-09-07: six failures reproduced on the old image. Shared validation and routing extraction
implemented; graph shrank to 732 lines. 52 affected and 301 full backend tests pass; nine live
journeys, lint, documentation/source-size and whitespace checks pass.
## Decisions
One helper owns citation presence; routing and persisted guardrails share it. Extract routing
instead of growing the 761-line legacy graph. Preserve existing valid policy configuration.
## Findings
The previous check passed any nonempty retrieval citation list even when the draft omitted it.
## Final Result
Completed 2026-09-07 for answer citation presence. See
[testing](../../testing.md#answer-citation-validation) for exact evidence and policy/quality limits.
Factual support and semantic retrieval remain open under the broader production goal.
