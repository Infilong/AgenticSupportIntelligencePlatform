# Model Budget Review Routing

## Goal
Convert model context and provider failures into inspectable graph state and human-review workflow outcomes instead of raw API failures.

## Audit Finding
Model settings could enforce context limits, but a provider exception during a LangGraph node could escape the graph execution path. That made the app behave less like a professional AI operations platform: a model-budget problem should be visible in trace, AI run ledger, guardrails, and review queue.

## Changes Made
- `MockModelProviderError` now carries the failed `AIRun` when available.
- `classify_intent` and `draft_response` graph nodes catch provider failures, record failed `GraphStep` entries, attach failed AI runs, and store failure state.
- Retrieval and drafting skip unnecessary work after a model-provider failure.
- Routing now sends model-provider failures to human review.
- Guardrails now emit `model_provider_failure` with high severity.
- Human review UI now shows model-budget failures with user-readable labels.
- Added regression coverage for a configured tiny classification context window that routes to human review with failed trace and failed AI run details.

## Verification
- `uv run pytest -s tests/test_agents.py::test_support_agent_routes_model_context_failure_to_human_review`
- `uv run ruff check .`
- `uv run pytest -s`

## Remaining Risks
- Context packing still does not proactively shrink prompts before provider call.
- The graph currently records failure and routes to review, but does not retry with a cheaper/smaller-context fallback model.
- Real provider adapter is still pending.

## Next Recommended Ticket
Add proactive token-budget planning in graph nodes: select model config before prompt assembly, trim/compress context to fit `max_context_tokens`, and only route to review when compression or fallback cannot make the call safe.
