# Structured Agent Review Context

## Goal
Make agent runs and human-review items understandable without reading raw trace JSON. The review queue should explain what happened, why the run was blocked, what evidence exists, and what the reviewer should do next.

## Implemented
- Changed classification from a plain intent string to a LangChain `PydanticOutputParser` result.
- Added structured classifier fields to graph state: intent, sentiment, product area, safety risk, escalation flag, confidence, and rationale.
- Updated routing so prompt injection, privacy complaints, high safety risk, and explicit escalation are visible route reasons.
- Kept sourced account-security answers eligible for finalization instead of over-routing every security request to review.
- Added computed `review_context` to human-review API responses, derived from persisted graph steps.
- Updated Review Queue UI to show:
  - recommended action
  - blocker labels and actions
  - classification signals
  - evidence counts and citations
  - clearer no-draft wording
- Added regression tests for structured classification output and review context.

## Architecture Notes
The database schema is unchanged. Structured state is stored in existing `GraphStep.output_json` and checkpoints. `HumanReviewResponse.review_context` is computed from the trace so the trace remains the source of truth.

## Why This Matters
A professional AI operations tool should not force reviewers to infer meaning from raw guardrail codes. Reviewers need clear decision context, while developers still need trace-level details for debugging.

## Verification
- `uv run ruff check .` -> passed
- `uv run pytest -s tests/test_langchain_support.py tests/test_agents.py tests/test_human_reviews.py` -> 25 passed
- `uv run pytest -s` -> 87 passed
- `npm run test` -> passed
- `npm run build` -> passed
- Docker rebuild: `docker compose up -d --build api frontend` -> passed
- Live review-context smoke -> passed; human-review API returned headline, recommended action, blockers, evidence, and structured classification
