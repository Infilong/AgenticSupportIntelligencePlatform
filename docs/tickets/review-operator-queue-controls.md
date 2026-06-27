# Review Operator Queue Controls

## Goal
Make the Human Review page behave more like a professional operations queue for reviewers and admins.

## Audit Finding
Human review had strong backend workflow semantics, but the UI still displayed pending reviews as an unsorted card list. Reviewers could not quickly filter critical items, separate evidence issues from model/token failures, or see queue composition before acting. That made the app feel less like an AI operations tool.

## Changes Made
- Added pending-review filters for all, critical, evidence, model/budget, and language cases.
- Added severity-first, newest-first, and oldest-first sorting.
- Added queue metrics for critical, evidence, model/budget, and currently visible items.
- Added severity badges to each pending review.
- Colored guardrail reason badges by risk level.
- Preserved direct trace inspection and finalization behavior.

## Verification
- `npm run test` -> passed
- `npm run build` -> passed
- `uv run ruff check .` -> passed
- `docker compose up -d --build frontend` -> rebuilt frontend and dependent API service
- `curl -I http://127.0.0.1:5173` -> 200 OK
- `curl http://127.0.0.1:8000/health` -> ok

## Remaining Risks
- The review page still lives inside the large single-file React app.
- Filtering is client-side; that is fine for local/small-team v1, but server-side pagination/filtering is needed for large queues.
- Reviewer assignment/ownership is not implemented yet.

## Next Recommended Ticket
Add reviewer ownership and queue assignment: claim/release review items, show assigned reviewer, and prevent accidental conflicting edits.
