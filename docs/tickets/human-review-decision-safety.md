# Human Review Decision Safety

## Goal
Remove a confusing and unsafe review behavior: a reviewer could approve a review item even when the agent produced no proposed answer.

## Context
The human review page previously showed cases like `citation_required, unsupported_answer, confidence_threshold` with "No proposed answer" while the decision control defaulted to approved. That made the app look inconsistent and toy-like.

## Changes
- Backend validation rejects `approved` when the review has no proposed answer.
- Backend validation rejects `edited` when no edited answer is provided.
- Frontend defaults no-answer reviews to `rejected` instead of `approved`.
- Frontend disables the "Approve proposed answer" option when no proposed answer exists.
- Review cards explain that no-answer cases should be rejected or resolved with a human-written edited response.

## Tests
- A reviewer cannot approve a missing proposed answer.
- A reviewer cannot submit an edited decision without an edited answer.
- A reviewer can reject a missing-answer review with comments.

## Verification
- `uv run ruff check .`
- `uv run pytest -s`
- `npm run test`
- `npm run build`

## Interview Notes
This is a concrete human-in-the-loop safety invariant: the UI helps the reviewer make the right choice, but the backend owns the rule. The system does not rely on frontend labels to prevent unsafe approval.
