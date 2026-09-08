# Atomic graph outcome publication
## Goal
Publish final graph status, final guardrails and any required review together.
## Context
AgentService commits completion before guardrails, then commits needs_human_review before the
queue record. Storage failure can expose premature success or leave no actionable review.
## Requirements
No final answer before final guardrails persist. Review routing and queue insertion are atomic.
On publication failure, roll back and mark the run failed without an answer where storage permits.
Preserve graph traces and model accounting already recorded during execution; never retry models.
## Non-goals
Durable graph resume, automatic retry after database outages or run-level budget reservations.
## Acceptance Criteria
Injected guardrail and review persistence failures never leave success or needs_human_review
without a queue entry. EN/JA/ZH review publication succeeds with matching workspace/run IDs.
Existing workflow, trace, review and isolation tests pass. Errors remain explicit.
## Plan
1. Reproduce partial publication with injected storage failures.
2. Extract outcome publication from AgentService into a cohesive transaction owner.
3. Stage guardrails and review before one commit; preserve original errors after rollback.
4. Verify affected workflows and browser journey; update owning reliability documentation.
## Verification
Failure-injection and multilingual tests, backend lint, source-size/docs checks and browser tests.
Preserve old-code failures and new-code results under .artifacts/20260907-review-publication/.
## Risks
Hidden intermediate commits, premature final answer visibility and failure-record storage errors.
Do not claim recovery if the database remains unavailable; retain original exceptions in that case.
## Progress
2026-09-07: confirmed separate commits in complete_graph_run, guardrail storage and queue insertion.
Six failure regressions fail on old code. Extracted graph_outcome.py, removed the premature
completion helper and staged final guardrails without a nested commit. Affected suite passes
48 tests; final publication suite passes 11 tests, including PostgreSQL visibility and secondary
failure persistence. Three browser journeys pass (19.4 seconds); lint and structural/docs gates
pass. Independent review reports no scoped P0/P1.
## Decisions
One helper owns final publication; node-level trace/model commits remain outside this transaction.
## Findings
Guardrail policy reads are side-effect free, so final checks can share the publication transaction.
Failure-record storage can also fail; preserve the original error and log only the secondary
error type. Interrupted processes and lost commit acknowledgments need separate recovery design.
## Final Result
Completed: final guardrails, run status/answer and review queue record publish atomically.
Injected failure leaves an explicit failed run when storage permits; no model calls are retried.
Evidence: .artifacts/20260907-review-publication/. Broader production acceptance remains open.
