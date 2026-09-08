# Dataset management audit atomicity
## Goal
Commit dataset moves/deletes and their attributable audit records together.
## Context
Dataset services commit before routes record audits, matching the repaired knowledge defect.
## Requirements
Rollback dataset, imports, examples, messages and labels on audit failure; preserve API permissions
and audit metadata; support corrected retry. Keep source modules below 300 lines.
## Non-goals
Import/label audit expansion, concurrent editing, folder deletion races, uncertain commit recovery.
## Acceptance Criteria
API failure injection restores all original rows; PostgreSQL observers see no uncommitted
mutation before audit commit. Successful retry adds one audit with the actual actor.
## Plan
1. Reproduce failed audit leaving a moved/deleted dataset.
2. Add a focused transaction helper; service owns audit, routes retain access checks.
3. Verify API rollback, PostgreSQL visibility, existing permissions and browser workflows.
## Verification
Ruff, affected pytest with PostgreSQL enabled, multilingual browser journeys and repository gates.
## Risks
Delete cascades must roll back too; preserve real dataset content in positive fixtures.
## Progress
2026-09-08 inspected move/delete and route audit boundaries; adding failure regressions.
Two API cases reproduced partial persistence (`.artifacts/dataset-audit/before.log`). Services
now require actor IDs and commit mutations/audits through `dataset_mutation.py`; route access
checks and audit metadata remain unchanged. Duplicate post-commit route audits were removed.
Ruff and 31 affected tests pass in 13.92s, including PostgreSQL observer/rollback/retry checks
(`backend-corrected.log`). Initial import-order failure remains in `backend.log`.
Four browser checks pass in 30.9s after mock API rebuild. Runtime has 543 HTTP outcomes and
zero server/error outcomes. Documentation/source-size (166 files)/whitespace gates pass.
## Decisions
Require actor ID on service mutations; keep audit action and metadata compatible.
## Findings
Move/delete currently commit before route audit.
## Final Result
Completed 2026-09-08. All scoped criteria verified, including child-row rollback and actor
attribution. No unresolved P0/P1 in this repair. Concurrent editing, import/label audit coverage
and uncertain-commit recovery remain separate work.
