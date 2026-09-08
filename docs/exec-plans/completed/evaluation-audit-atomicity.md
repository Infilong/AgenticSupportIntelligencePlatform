# Atomic evaluation management audits
## Goal
Commit evaluation move/archive/delete with their actor-attributed audit or roll everything back.
## Context
Routes currently write audits after EvaluationRunner commits the mutation. Audit failure can
therefore return an error after durable movement, archival or deletion of evaluation evidence.
## Requirements
Preserve permissions, response contracts, audit metadata and active-reservation deletion guard.
Keep evaluator size declining by extracting management transactions into one focused owner.
## Non-goals
Concurrent evaluation execution recovery, provider billing changes or complete audit coverage.
## Acceptance Criteria
Injected audit failures preserve evaluation/accounting rows; retries succeed with exactly one
audit. PostgreSQL observers cannot see changes before audit commit. Relevant permission tests pass.
## Plan
1. Reproduce the three API failures with populated results/accounting evidence.
2. Extract management transactions; pass authenticated actor from routes and remove duplicate audits.
3. Verify PostgreSQL isolation, rollback, retry, permissions and browser workflow; update docs.
## Verification
Affected mock backend tests with PostgreSQL enabled, Ruff, rebuilt API/browser checks,
source-size baseline reduction, documentation and whitespace checks. Preserve failing evidence.
## Risks
Permanent deletion affects results, cases, metrics and reservation references. Keep the existing
reservation guard and verify those rows after failure. No schema migration is needed.
## Progress
2026-09-08: inspected routes/services; added three API audit failure regressions.
All three reproduced durable mutations after audit failure. Extracted evaluation_management.py;
routes pass actors and no longer commit audits separately. Ruff and 28 affected tests pass,
including three PostgreSQL visibility/rollback/retry cases. Rebuilt API passes four browser
checks; 543 HTTP outcomes show no server/errors. Lowered size baselines to 496/328 lines.
Evidence and exact commands: [testing](../../testing.md#evaluation-management-audit-atomicity).
## Decisions
Keep route-facing EvaluationRunner methods while delegating transaction ownership to a small module.
## Findings
Original commits preceded route-level audit writes for all three mutations. Failure injection
confirmed the partial durability. The shared transaction repairs that boundary; active model
reservations still prevent deletion. Formatting failures were corrected and retained as evidence.
## Final Result
Completed 2026-09-08: all acceptance checks pass for management/audit atomicity. No schema or
role-policy change. Concurrent execution recovery and ambiguous commit acknowledgments remain open.
