# Restricted-role browser verification

## Goal
Verify real restricted-role browser behavior together with server-enforced denial and isolation.
## Context
Backend workflow denial tests use execution spies; browser coverage includes reviewer visibility
but lacks forged-request checks, ledger invariance and reviewer resolution in one real-role journey.
## Requirements
Use real users, memberships and live API responses. Verify allowed reads/retrieval and review
actions, denied mutations, foreign resource IDs, preserved sessions and no usage from denied work.
## Non-goals
Changing permission policy, mocking membership responses, or claiming every route is covered.
## Acceptance Criteria
Viewer/reviewer browser journeys pass; forged denied mutations return 403, foreign reads/search
return 404, and foreign document filters yield no chunks. Denied work leaves usage/run counts
unchanged. Reviewer resolution persists; viewer cannot resolve. No browser exceptions occur.
## Plan
1. Inspect existing permission map and backend/browser verification.
2. Add separate fixture and browser denial journey using synthetic scoped resources.
3. Run focused tests, backend pre-execution denial tests and the complete browser suite.
4. Record exact coverage, results and remaining gaps.
## Verification
Playwright restricted-role-security and full suite against PostgreSQL; backend
test_workflow_authorization with SQLite fixtures and execution spies. Retain
.artifacts/restricted-roles/ logs and traces; do not conflate these database boundaries.
## Risks
Hidden UI controls are not authorization. Unchanged cost alone does not prove no provider call;
pair live browser evidence with server tests that fail if denied execution reaches providers.
## Progress
2026-09-08: inspected current role map, permission dependencies and prior tests. Added viewer
and reviewer fixtures/journeys, then ran focused verification; application code unchanged.
Final verification: 24 Chromium tests passed in 55.1s; seven backend execution-spy tests passed
in 13.88s with one existing dependency deprecation warning. Documentation/size/whitespace gates
pass. Live API window: 2,376 HTTP outcomes, zero server failures; mock embeddings and no provider
key verified. Evidence is retained in [testing](../../testing.md#restricted-role-browser-verification).
## Decisions
Keep setup and assertions separate; no new dependencies or broad application changes.
## Findings
Existing browser reviewer test verifies visibility but does not submit a review decision.
The first viewer test expected a disabled Resolve review button; the UI correctly labels that
disabled control Read only. Updated the selector and retained the failed trace. Its forged
viewer resolution request had already returned 403; no permission policy change was needed.
## Final Result
Completed 2026-09-08. Two real-role browser journeys verify allowed retrieval, foreign-resource
isolation, denied mutation responses and usage invariance; reviewer rejection persists and
viewer resolution is denied. Backend spies verify pre-execution denial independently. This
does not establish every role/route combination, concurrency or real-provider quality.
Application code and dependencies were unchanged; the broader production goal remains active.
