# Workflow authorization boundaries
## Goal
Prove denied workflow requests cannot disclose protected resources or enter AI execution.
## Context
The multilingual owner workflow passes. Existing isolation checks do not comprehensively
assert that denied operations stop before retrieval, graph execution or evaluation begins.
## Requirements
Test anonymous users, outsiders, viewers, reviewers and developers against populated resources.
Use valid payloads and owner-positive controls; assert denial, no content leakage and no AI ledger changes.
## Non-goals
Complete route enumeration, multi-user browser UX, penetration testing or production certification.
## Acceptance Criteria
Protected reads deny anonymous/outsider access; forbidden mutations fail before execution;
reviewers and developers retain distinct permissions; allowed reviewer resolution succeeds.
## Plan
1. Inspect permission dependencies and workflow service entry points.
2. Add one focused regression file using actual resources and execution spies.
3. Run tests/lint, investigate failures and document precise coverage limits.
## Verification
Docker deterministic backend tests with existing fixtures; preserve logs under
`.artifacts/20260907-workflow-authorization/`. Compare ledger counts around denied requests.
## Risks
Invalid fixtures can produce misleading denials. Positive owner reads establish that tested
paths exist; payloads are valid and expected codes distinguish authentication from membership.
## Progress
2026-09-07: inspected role maps/dependencies and added populated-resource matrix/execution spies.
Thirteen affected tests pass in 14.08 seconds; final lint passes. No application change needed.
## Decisions
Exercise real FastAPI dependencies; do not mock authorization or infer server safety from UI controls.
## Findings
All current roles may read knowledge, so retrieval denial applies to anonymous users and outsiders.
Reviewer cannot import or evaluate; developer cannot resolve human review.
## Final Result
Completed 2026-09-07 for the specified workflow entry boundaries. See
[testing](../../testing.md#workflow-authorization-boundary-verification) for coverage, fixture/lint
failures and limits. Every-route coverage and multi-user browser denial remain separate work.
