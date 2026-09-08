# Folder hierarchy cycle integrity
## Goal
Reject descendant folder moves, including concurrent opposing moves, without corrupting hierarchy.
## Context
Folder updates reject only direct self-parenting. Indirect cycles can make folders undeletable.
## Requirements
Workspace/type-scoped ancestry validation before mutation; concurrent PostgreSQL updates must
not both admit opposing parent assignments. Explicit move to root remains available.
## Non-goals
Repairing existing corrupt data automatically, distributed trees, full delete/audit atomicity.
## Acceptance Criteria
Direct/indirect descendant moves return 400 with unchanged state. Valid moves succeed.
Concurrent opposing moves admit exactly one transition and leave an acyclic tree.
## Plan
1. Reproduce API failures across all four resource types.
2. Serialize parent updates on the workspace and validate the proposed ancestry before writes.
3. Verify stale-session concurrent PostgreSQL moves, existing PATCH and permission regressions.
## Verification
Deterministic API cases, real PostgreSQL concurrency, lint, size/docs gates and live browser smoke.
## Risks
Locks must release on commit/rollback; avoid foreign-key lock upgrades. Read fresh ancestry
after admission rather than stale ORM identity-map values. No model calls or new migration.
## Progress
2026-09-08 inspected service update flow and added descendant-move reproductions.
Four API cases fail against the prior image; opposing PostgreSQL moves also reproduce a
cycle. Parent updates now lock the workspace and read fresh ancestry; stale folder instances
are refreshed before assigning a new parent. Backend lint and 37 affected tests pass,
including two PostgreSQL tests. Browser verification is pending.
## Decisions
Use the existing workspace as the serialization boundary for parent changes; one owner.
## Findings
Current validation only compares the folder ID to the proposed immediate parent.
## Final Result
Completed 2026-09-08. Four reproduced API failures and opposing PostgreSQL moves are repaired.
All 37 affected backend tests (two PostgreSQL cases), lint and three browser checks pass.
Runtime: 235 HTTP outcomes, zero server/error outcomes. Documentation/source-size/whitespace
gates pass. See [verification](../../testing.md#folder-hierarchy-cycle-integrity).
Existing corrupt data is not automatically changed; folder/audit atomicity and concurrent
resource assignment/deletion remain outside this verified parent-move contract.
