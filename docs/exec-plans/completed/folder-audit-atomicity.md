# Atomic folder mutations and audit
## Goal
Prevent folder changes from committing without their audit record.
## Context
Create/update/delete currently commit inside the service, then the route commits the audit.
## Requirements
Stage folder mutation and audit together; rollback and re-raise failed persistence. Preserve
permissions, hierarchy locks, metadata and API responses. Explicit actor identity at mutation.
## Non-goals
External audit delivery, ambiguous commit acknowledgment recovery, concurrent resource deletion.
## Acceptance Criteria
Injected audit failures leave folders/audit unchanged for create/rename/delete; retry succeeds
with exactly one new audit record. Existing permissions and PostgreSQL hierarchy tests pass.
## Plan
1. Reproduce partial commits with API failure injection.
2. Move folder audit persistence into the mutation service and remove route-level double commits.
3. Verify failure/retry, hierarchy concurrency and browser management paths.
## Verification
Affected backend tests, PostgreSQL cases, lint and live folder browser checks; retain failures.
## Risks
Keep the service below 300 lines; rollback must preserve the original error. Do not hold locks
beyond the database transaction. Internal callers must supply an attributable actor.
## Progress
2026-09-08 inspected service and route commit boundaries and added failure-injection cases.
## Decisions
One service owns the folder and audit transaction; routes retain authorization/error mapping.
## Findings
AuditLogService currently commits separately after the folder service has returned.
## Final Result
Completed 2026-09-08: reproduced all three partial-commit failures, moved audit staging into
the mutation service and removed duplicate route commits. All 43 affected tests, including
five PostgreSQL cases, backend lint and five browser checks pass. Runtime records 482 HTTP
outcomes without server/error outcomes. Repository gates pass; service remains 282 lines.
See [evidence](../../testing.md#atomic-folder-mutation-audit). Uncertain commit acknowledgment
and resource assignment/deletion concurrency remain separate requirements.
