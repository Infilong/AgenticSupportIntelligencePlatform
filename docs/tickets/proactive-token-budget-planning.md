# Proactive Token Budget Planning

## Goal
Prevent avoidable model-call failures by checking active model context limits before the LangGraph workflow calls the model.

## Audit Finding
The platform could enforce model context limits at the provider boundary, but that was reactive. A professional AI platform should plan model calls before execution: reject oversized classification requests without spending a model call, trim retrieved RAG context before drafting, and expose those budget decisions in trace.

## Changes Made
- Extended `TokenBudgetPlanner` with `plan_model_call`, which estimates prompt/completion tokens against active model pricing/context limits.
- Added proactive classification budget checks before `run_classification_chain`.
- Added draft-response context fitting that drops lower-ranked retrieved chunks until the prompt fits the active draft model context window.
- Added graph-state fields for `model_budget_failure`, `token_budget_action`, and `trimmed_context_count`.
- Added `model_budget_failure` guardrail routing to human review when a call cannot fit safely.
- Updated trace signals to show token-budget action, trimmed chunk count, and model-budget failure without opening raw JSON.
- Added tests for planner decisions, proactive classification budget routing, and draft context trimming.

## Verification
- `uv run pytest -s tests/test_ai_observability.py::test_model_call_budget_planner_uses_active_context_window tests/test_agents.py::test_support_agent_routes_proactive_model_budget_failure_to_human_review tests/test_agents.py::test_support_agent_trims_retrieved_context_before_draft_model_call`
- `uv run ruff check .`
- `uv run pytest -s`
- `npm run test`
- `npm run build`
- `docker compose up -d --build api frontend`
- Live API smoke confirmed a constrained draft model trimmed two retrieved chunks and finalized with `510/512` tokens.

## Current Evidence
Live smoke result:

```json
{
  "run_status": "completed",
  "route_decision": "finalize",
  "budget_action": "trimmed_retrieved_context",
  "trimmed_context_count": 2,
  "remaining_chunks": 2,
  "draft_model": "mock-trim-drafter",
  "draft_tokens": 510
}
```

## Remaining Risks
- Context fitting only drops lower-ranked chunks; it does not summarize or compress chunks yet.
- Classification over-budget cases route to review; there is no cheaper fallback classifier path yet.
- The provider is still mock; real provider abstraction remains pending.

## Next Recommended Ticket
Add a real OpenAI-compatible provider adapter behind the existing provider interface, keeping all automated tests on mock providers and ensuring real calls still write `AIRun` ledger entries.
