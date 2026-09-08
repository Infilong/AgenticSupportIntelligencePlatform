# Folder mutation authorization
## Goal
Prove denied callers cannot execute folder management or change persisted state.
## Context
Existing folder tests cover owner workflows and selected denials; execution-order and
unchanged audit/state proof is incomplete across resource types.
## Requirements
Real authentication and workspace dependencies; populated owner-positive fixtures; anonymous,
outsider, viewer and reviewer denial for all four folder resource types.
## Non-goals
Full role-by-route certification, folder hierarchy repair, new permissions or UI changes.
## Acceptance Criteria
Create/rename/delete return 401/404/403 as appropriate before service entry, with identical
folder and audit snapshots. Existing owner management and foreign-folder tests still pass.
## Plan
1. Add an independent parameterized API regression module.
2. Run folder and workflow authorization suites with lint; fix defects if exposed.
3. Record exact evidence and remaining coverage gaps.
## Verification
Mock-provider backend tests with real permission dependencies and service-entry observations.
## Risks
An empty resource or mocked authorization could yield false confidence; use populated records
and preserve normal domain behavior in observation wrappers.
## Progress
2026-09-08 inspected folder routes/service/tests and added the 16-case mutation matrix.
## Decisions
Keep permission proof separate from implementation; no new runtime abstraction is needed.
## Findings
Folder mutation routes use resource_folders:manage; reads have type-specific permissions.
## Final Result
Completed 2026-09-08. All 16 new cases and existing owner/foreign-folder/workflow regressions
pass: 34 tests in 26.50s, backend lint, documentation/source-size and whitespace checks.
No application defect found or runtime code changed. Evidence is recorded in
[testing](../../testing.md#folder-mutation-authorization-boundary). SQLite permission evidence
does not establish concurrency or full management-route coverage.
