# Atomic human-review transitions

## Goal
Prevent competing reviewers from overwriting assignments or terminal decisions, and keep the
review, graph outcome, checkpoint and audit consistent.
## Context
HumanReviewService.claim/release/resolve read current state then commit unconditional ORM writes.
There is no row lock or conditional update. Resolve updates graph/checkpoint in the same commit,
but the API records its audit in a second commit. Request authorization is already a dependency.
The default test fixture uses SQLite, which cannot establish PostgreSQL locking behavior.
## Requirements
Serialize mutations of one workspace-scoped review. Recheck assignment and pending state after
acquiring ownership of the transition; refresh stale ORM state. Preserve existing 404/409 errors.
Only one terminal decision and checkpoint may win. Audit and state must commit together.
## Non-goals
Durable graph resume, model spending admission, redesign of the review queue, or paid model calls.
## Acceptance Criteria
Concurrent claim attempts have one owner; another reviewer receives an assignment conflict.
Concurrent resolve attempts yield one terminal result and one checkpoint/audit event.
Release cannot clear a newer claim. Cross-workspace and denied-role requests remain rejected.
Injected persistence failure rolls back all transition records. PostgreSQL tests demonstrate
these outcomes with independent sessions and controlled overlap, not timing-only sleeps.
## Plan
1. Add a failing PostgreSQL concurrency reproduction with isolated disposable test data.
2. Extract transition ownership from the oversized service into a cohesive helper if required;
   keep queue querying separate and lower the service size baseline after extraction.
3. Serialize claim/release/resolve, refresh state, and bring audit into the same transaction.
4. Verify success, conflicts, isolation, rollback, and browser review behavior.
## Verification
Run focused existing review API tests and new PostgreSQL tests; preserve old-code failures.
Use a dedicated test database/schema with independent sessions and bounded synchronization.
Run backend lint, source-size and docs gates, then the browser review journey.
Inspect persisted review, run, checkpoint and audit records after competing requests.
## Risks
Lock ordering, stale SQLAlchemy identity-map values, error paths retaining locks, and audit
duplication. Keep transactions short and use bounded test deadlines. Do not run destructive
fixture setup against the verification application's populated database.
## Progress
2026-09-07: inspected service, route, audit and session ownership. Four regressions fail against
the old image after fixing isolated-schema visibility of the pgvector type. Added a small
transaction helper; existing service/API shrink. Row locks and refreshed ORM state serialize
transitions; audit moves from the route into the state commit. Initial 13 affected tests and
three browser journeys pass. Added stale-session coverage and enabled PG checks in local/CI
harnesses. Full backend regression passed 239 tests (including five PostgreSQL cases); final
lint, source-size and documentation gates pass. Independent review found no scoped P0/P1.
## Decisions
Treat this as a high-risk concurrency boundary; SQLite passing tests alone are insufficient.
Preserve API semantics while moving mutation ownership into one transaction.
## Findings
Assignment checks are duplicated across three methods. Each route records audit after the
service has committed; audit failure can report an error after the state was already changed.
That split is now removed. Separate remaining gap: AgentService.run_agent commits a graph's
needs_human_review state before create_pending commits its review. Interrupted creation can
leave a run with no actionable queue record; repair this publication boundary next.
## Final Result
Completed 2026-09-07: competing claim/release/resolve and stale sessions cannot overwrite the
winner; audit insertion failure rolls back review, run and checkpoint. Existing review API
tests retain permission/isolation behavior. Evidence: `.artifacts/20260907-review-transactions/`.
The broader production objective, initial review publication, and budget admission remain open.
