# Human Review No-Draft Guard

## Goal
Make the human review workbench clearer and safer when a blocked LangGraph run has no proposed model answer.

## Context
The backend already returns structured review context with blockers, evidence, classification, recommended action, and `can_approve`. The frontend used a fallback from `run.final_answer` when building pending review drafts, which could make a review appear approvable even when the review record had no proposed answer.

## Requirements
- Pending reviews should only allow approval when the backend review context says approval is allowed and a proposed answer exists.
- No-draft cases should clearly tell reviewers that a human response or rejection is required.
- Edited decisions should require a non-empty human-approved answer before resolving.
- Keep trace inspection and claim/release controls unchanged.

## Non-goals
- Do not change backend review resolution semantics.
- Do not redesign the entire review page.
- Do not add fake review content.

## Implementation
- Updated review draft initialization to use `review.proposed_answer` and `review_context.can_approve` instead of falling back to `run.final_answer`.
- Added a no-proposed-answer callout in the pending review detail.
- Updated decision copy from generic editing to explicit human-approved answer language.
- Disabled resolution when the selected decision cannot be submitted safely.

## Validation
- `cd frontend && npm run build` passed.
- `cd backend && uv run pytest -s -q tests/test_human_reviews.py` passed: 7 passed, 1 warning.
- Browser QA was not rerun because WSL Playwright Chromium remains blocked by the missing `libnspr4.so` dependency and sudo requires a password.

## Human Review Checklist
- Confirm pending no-source cases show that no proposed answer exists.
- Confirm the approve option is disabled when no safe draft exists.
- Confirm reviewers can still write an answer, reject the run, claim/release, and inspect trace.

## Interview Notes
This ticket demonstrates product integrity in human-in-the-loop AI workflows: the UI must reflect backend safety state and should not let reviewers approve output that the workflow did not produce as an approvable draft.
