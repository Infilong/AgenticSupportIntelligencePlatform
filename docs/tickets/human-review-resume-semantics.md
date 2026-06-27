# Human Review Resume Semantics

## Goal
Make human review resolution part of the stateful agent workflow instead of a disconnected approval record.

## Audit Finding
The app routed risky or unsupported graph runs to human review, but resolving a review only updated the `HumanReview` row. The associated `GraphRun` remained stuck in `needs_human_review`, and Trace Explorer had no post-review checkpoint. That made the workflow feel unfinished and weakened the stateful LangGraph operations story.

## Changes Made
- When a review is approved, the associated graph run is completed with route `human_approved` and the proposed answer becomes the final answer.
- When a review is edited, the associated graph run is completed with route `human_edited` and the edited answer becomes the final answer.
- When a review is rejected, the graph run is marked failed with route `human_rejected` and no final answer.
- Every terminal review decision writes a compact `human_review_*:after` checkpoint attached to the original graph run.
- Trace checkpoint ordering is now deterministic by workflow order, with post-review checkpoints after graph node checkpoints.
- Resolved review history now shows final run status/route and links directly to the finalization trace.
- Tests cover edited finalization, rejected finalization, trace checkpoint visibility, duplicate-resolution protection, and workspace isolation.

## Verification
- `uv run pytest -s tests/test_human_reviews.py tests/test_agents.py::test_support_agent_run_persists_trace_tool_calls_and_ai_runs` -> 7 passed
- `uv run ruff check .` -> passed
- `uv run pytest -s` -> 85 passed
- `npm run test` -> passed
- `npm run build` -> passed
- `docker compose up -d --build api frontend` -> rebuilt and restarted
- Live API smoke -> review-routed run resolved to `completed`, route `human_edited`, final answer persisted, and trace ended with `human_review_edited:after`

## Current Scope
This implements post-review finalization semantics and checkpoint visibility. It does not yet re-enter a compiled LangGraph runtime to execute a new graph node; the checkpoint is persisted by the application service as the durable resume/finalization event.

## Remaining Risks
- Full LangGraph-native interrupt/resume remains future work.
- Rejected runs are marked `failed`, which is appropriate for unsupported output but may later need a separate terminal status such as `rejected`.
- The frontend still uses one large React file; the review and trace workbenches should be extracted into feature components.

## Next Recommended Ticket
Improve the Review UI as an operator queue with filtering, reviewer ownership, severity sorting, and a compact explanation of what changed in the graph run after resolution.
