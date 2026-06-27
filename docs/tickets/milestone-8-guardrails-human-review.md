# Milestone 8: Guardrails And Human Review

## Goal
Add practical guardrails and a real human review workflow. Unsupported, unsafe, low-confidence, or citation-poor graph runs should not only set a route flag; they should create auditable guardrail results and pending human review records.

## Context
Implemented foundation:
- LangGraph support-agent workflow with graph steps/tool calls.
- Retrieval citations and no-source routing.
- AI run ledger and token/cost tracking.
- Workspace-scoped APIs.

## Requirements
- Add models and migration for:
  - `GuardrailResult`
  - `HumanReview`
- Add deterministic guardrails:
  - prompt injection check.
  - citation-required check.
  - unsupported/no-source check.
  - language preservation check.
  - confidence threshold check.
- Add human review API:
  - `GET /api/v1/workspaces/{workspace_id}/human-reviews`
  - `GET /api/v1/workspaces/{workspace_id}/human-reviews/{review_id}`
  - `POST /api/v1/workspaces/{workspace_id}/human-reviews/{review_id}/resolve`
- Create `HumanReview` records when graph run route is `human_review`.
- Let reviewers approve, edit, or reject proposed answers.
- Enforce workspace isolation for guardrails and human reviews.
- Add tests for prompt injection, missing citations/no-source, review create/list/detail/resolve, and cross-workspace denial.

## Non-goals
- No frontend review UI yet.
- No real safety classifier model.
- No policy/tone LLM judge.
- No complex role hierarchy.
- No external ticket/email integration.

## Design Plan
- Add `backend/app/models/review.py`.
- Add `backend/app/services/guardrails.py`.
- Add `backend/app/services/human_review_service.py`.
- Update `SupportAgentGraphRunner` / `AgentService` to log guardrails and create review records.
- Add `backend/app/schemas/human_review.py`.
- Add `backend/app/api/v1/human_reviews.py`.
- Add migration `0007_guardrails_human_review.py`.
- Add tests and docs/learning note.

## Database Migrations
```text
GuardrailResult
- id
- workspace_id
- graph_run_id
- graph_step_id nullable
- guardrail_type
- passed
- severity
- message
- created_at

HumanReview
- id
- workspace_id
- graph_run_id
- reviewer_id nullable
- reason
- proposed_answer nullable
- reviewer_decision: pending / approved / edited / rejected
- edited_answer nullable
- comments nullable
- created_at
- resolved_at nullable
```

## Acceptance Criteria
- low-confidence/no-source graph runs create pending human review.
- prompt injection creates guardrail result and routes to review.
- missing citations creates guardrail result and routes to review.
- reviewer can approve/edit/reject.
- workspace isolation is tested.
- validation passes and commit is pushed.

## Risks
- Guardrails can look fake if presented as comprehensive safety. Document them as deterministic practical checks.
- Human review should be a workflow record, not just a status flag.
- Do not make guardrails depend on real LLM calls in tests.

## Interview Notes
Be able to explain:
- why deterministic guardrails are useful before model-based judges.
- why unsupported/no-source cases must route to review.
- how guardrail records help audit and debugging.
- how human review changes the product from a chatbot to an operational AI system.


## Implementation Record
Completed implementation details:
- Added `backend/app/models/review.py` with `GuardrailResult` and `HumanReview`.
- Added migration `0007_guardrails_human_review.py`.
- Added deterministic guardrail service and human review service.
- Integrated guardrail evaluation and pending review creation into `AgentService.run_agent`.
- Added human review APIs for list/detail/resolve.
- Added `backend/tests/test_human_reviews.py`.
- Updated architecture, API, security, LangGraph, learning, and ticket docs.

Important decisions:
- Guardrails run after graph execution in v1 to keep LangGraph nodes focused.
- Blocking guardrails can override a finalize decision and route to human review.
- Deterministic checks are documented as practical v1 controls, not comprehensive safety.
- Human review is a real workflow record with reviewer, decision, edited answer, comments, and resolution time.

Validation results:
- `make backend-lint`: passed.
- `make backend-test`: 49 passed, 1 existing TestClient deprecation warning.
- `make backend-migrate`: passed against Docker PostgreSQL/pgvector.
- Docker API smoke: prompt injection run created pending human review and review was resolved as edited.

Self-review result:
- No unresolved P0/P1 issues found.
- P2: guardrails are deterministic pattern/rule checks and should not be marketed as comprehensive safety.
- P2: frontend review UI is not implemented yet.
- P2: guardrail evaluation currently runs after graph execution; future workflows may add earlier blocking nodes.
