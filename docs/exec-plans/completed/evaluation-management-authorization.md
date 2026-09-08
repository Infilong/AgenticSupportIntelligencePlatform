# Evaluation management authorization
## Goal
Verify protected evaluation reads and mutations reject unauthorized callers before service entry.
## Context
Existing workflow tests cover execution denial and some reads, but not comparison, move,
archive and permanent deletion as a complete management boundary.
## Requirements
Use real authentication/permission dependencies and populated evaluation results, metrics and
accounting records. Verify permitted reads and denial without disclosures or state changes.
## Non-goals
Changing role policy, transaction atomicity, complete route coverage or real-provider quality.
## Acceptance Criteria
Anonymous, outsider, reviewer, viewer, member and developer denial cases pass; permitted reads
remain available; service-entry observers remain empty and stored evidence remains unchanged.
## Plan
1. Inspect routes, role policy and existing workflow fixtures.
2. Add one focused management regression module using the existing populated fixture.
3. Run lint and affected evaluation/authorization tests; review and record scope.
## Verification
Mock-provider backend tests in the isolated verification container. Snapshot evaluation cases,
runs, results, metrics, AI ledger, reservations and audit rows after every denied operation.
## Risks
Empty fixtures or invalid IDs could make denials meaningless. Create an archived baseline for
permanent deletion and assert positive reads before observing denied entry points.
## Progress
2026-09-08 resource-ID follow-up: added two owner-of-both-workspaces cases covering 18 foreign
evaluation/folder requests, both comparison operands and rejected creation before model calls.
Positive reads succeed; denied requests preserve evaluation/accounting/audit snapshots. Ruff
and 28 affected tests pass. [Evidence](../../testing.md#evaluation-resource-workspace-isolation).
No application change or browser rerun; concurrent resource races remain outside this scope.
2026-09-08: inspected policy/routes; added six actor cases covering 26 denied requests.
Ruff and all 26 affected tests pass in 26.45s, with the existing Starlette/httpx warning.
Evidence: `.artifacts/evaluation-authorization/backend.log`. No application change was needed.
## Decisions
Preserve real services with pass-through observers; do not replace authorization dependencies.
## Findings
Real dependencies reject every tested denial before service entry; allowed reads expose the
populated fixture and archived baseline. Evaluation move/archive/delete currently commit before
their route writes the audit record. Audit failure atomicity needs a separate reproduction/repair.
## Final Result
Completed 2026-09-08. Named management denials preserve stored evaluation/accounting/audit
evidence. The follow-up also verifies named cross-workspace ID combinations. This does not establish
archived-workspace management policy or a complete application permission matrix. Audit atomicity
was repaired separately in the [evaluation audit plan](evaluation-audit-atomicity.md).
