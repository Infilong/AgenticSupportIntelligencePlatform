# Knowledge management authorization
## Goal
Verify denied document-management requests stop before protected execution and preserve data.
## Context
Knowledge routes declare read/write/folder/delete permissions. Existing owner and foreign-ID
tests cover successful management and scoping; denied service entry needs direct evidence.
## Requirements
Real authentication and role dependencies; populated documents; no indexing, mutation or audit
side effects after denial. Preserve existing permission semantics.
## Non-goals
Changing roles, audit transaction redesign, full application permission certification.
## Acceptance Criteria
Anonymous/outsider/read-only roles cannot upload, reindex, move or delete; member/developer
restrictions are verified separately. Snapshots and service-entry observers prove denial.
Existing successful and workspace-scoped knowledge tests remain green.
## Plan
1. Inspect routes, role permissions, service boundaries and existing tests.
2. Add focused authorization regressions in one new test module.
3. Run knowledge and authorization tests with mocks; review evidence and update owning docs.
## Verification
Ruff, focused pytest suite, documentation and source-size checks, whitespace review.
## Risks
Empty fixtures and mocked permission dependencies can create false confidence; use real
API-created indexed documents and real memberships. SQLite checks do not prove concurrency.
## Progress
2026-09-08 inspected route dependencies and role policy; implementing service-entry evidence.
Completed six actor cases with 19 denied operations, populated indexed documents, permitted
member reads and unchanged full-row document/version/chunk/embedding/AI-run/audit snapshots.
Ruff and 38 affected tests pass in 16.93s; one existing Starlette/httpx deprecation warning.
Evidence: `.artifacts/knowledge-authorization/backend.log`. No application behavior changed.
## Decisions
Observe normal methods without replacing their behavior; compare persisted rows after each denial.
## Findings
Document indexing and audit transactions are separate concerns from permission admission.
## Final Result
Completed 2026-09-08. All scoped acceptance criteria pass through real API dependencies.
Existing owner management and foreign-workspace tests remain green. Full permission coverage,
authorized-write audit atomicity and concurrent management integrity remain separate work.
