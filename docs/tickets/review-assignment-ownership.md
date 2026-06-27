# Review Assignment Ownership

## Goal
Make the human-review queue safer for team operation by allowing reviewers to claim and release pending review items.

## Audit Finding
The queue could filter and sort risk, but pending reviews were still effectively unowned. In a real AI operations team, two reviewers should not accidentally work on the same case, and the UI should make ownership visible before finalizing a run.

## Changes Made
- Added `GET /api/v1/auth/me` so the frontend can identify the current reviewer.
- Added workspace-scoped review ownership APIs:
  - `POST /api/v1/workspaces/{workspace_id}/human-reviews/{review_id}/claim`
  - `POST /api/v1/workspaces/{workspace_id}/human-reviews/{review_id}/release`
- Reused `HumanReview.reviewer_id` for pending assignment and terminal reviewer attribution.
- Enforced assignment conflicts: a review assigned to another user cannot be released or resolved by the current user.
- Added audit events for claim and release actions.
- Added frontend queue filters for `Mine` and `Unassigned`.
- Added claim/release controls and owner state on pending review cards.

## Verification
- `uv run pytest -s tests/test_human_reviews.py tests/test_auth_workspace.py` -> 16 passed
- `uv run ruff check .` -> passed
- `uv run pytest -s` -> 86 passed
- `npm run test` -> passed
- `npm run build` -> passed

Runtime smoke:
- `docker compose up -d --build api frontend` -> rebuilt and restarted
- Live API smoke -> `/auth/me` returned current user, claim set `reviewer_id`, release cleared `reviewer_id`, and audit logs recorded `human_review.claimed` / `human_review.released`

## Current Scope
This provides lightweight ownership for a local small-team queue. It does not implement role-based reviewer permissions or admin reassignment.

## Remaining Risks
- Any workspace member can claim a pending review; role-based reviewer/admin permissions are future work.
- There is no explicit `assigned_at` timestamp yet.
- The frontend still uses client-side filtering and a large single-file React implementation.

## Next Recommended Ticket
Add reviewer/admin role controls or explicit review assignment metadata such as `assigned_at` and assignment history.
