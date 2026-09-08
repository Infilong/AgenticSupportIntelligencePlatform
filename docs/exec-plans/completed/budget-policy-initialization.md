# Concurrent budget policy initialization
## Goal
Prevent first-use Costs and budget-policy requests from failing during concurrent initialization.
## Context
A passing browser screenshot exposed a shell fetch-error toast. The isolated API log records
request `21548eed-34ef-45cf-b2cf-104d7c345bb6`, GET budget-policy, status 500, IntegrityError.
The traceback identifies the unique workspace constraint during get_or_create insertion.
## Requirements
One policy per workspace; concurrent initializers return the same policy. Preserve existing
values, permission boundaries and admission lock ordering. Do not hide database errors.
## Non-goals
Provider retries, CORS redesign, broad frontend loading refactor or production certification.
## Acceptance Criteria
Deterministic PostgreSQL races reproduce before repair and pass afterward. Relevant backend
and browser checks pass; live API logs show no recurrence during verification.
## Plan
1. Preserve logs and reproduce synchronized missing-policy reads.
2. Let BudgetPolicyService own the missing-policy lock/recheck/insert transaction.
3. Verify against policy and embedding initializers, then full backend/browser tests.
4. Record evidence and update reliability guidance.
## Verification
Artifacts: `.artifacts/20260908-fetch-diagnosis/`. Tests synchronize the first SQL reads before
either insert; inspect row count and returned policy identity. Rebuild only the isolated API
in mock mode before browser checks. Retain failed test output and API logs.
## Risks
Lock order must match admission: workspace then policy. Release the initialization lock before
returning. Existing get_or_create may commit its caller session on creation; this focused fix
retains that contract. It does not add an independently committing ledger path.
## Progress
2026-09-08: inspected the API traceback. Both synchronized regressions fail with uniqueness
errors before repair. Added workspace NO KEY UPDATE and a second policy read before insertion.
Eleven focused tests and Ruff pass. Rebuilt API passes all 12 browser tests plus 24 simultaneous
first-use HTTP reads across three fresh workspaces. Rebuilt API logs have zero HTTP 5xx records.
Full backend verification passes 402 tests in 219.55 seconds; evidence is in testing.md.
## Decisions
Use the existing workspace serialization contract so policy and embedding creation cooperate;
do not broadly catch IntegrityError or retry arbitrary transactions.
## Findings
Frontend startup loads Costs and budget policy concurrently. Lazy initialization was an
unprotected SELECT/INSERT. A green behavioral test did not establish clean HTTP outcomes.
## Final Result
Completed 2026-09-08. Synchronized before/after PostgreSQL tests prove the initialization race
and repair. Full backend, browser, concurrent live requests, lint, documentation/source-size
and whitespace checks pass. One existing dependency deprecation warning remains. No claim is
made about unrelated network failures or complete production readiness.
