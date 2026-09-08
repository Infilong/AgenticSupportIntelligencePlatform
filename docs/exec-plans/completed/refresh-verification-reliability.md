# Refresh verification reliability
## Goal
Repair recurring full-suite refresh failures using measured causes rather than blind retries.
## Context
Full run `.artifacts/20260907T193400016Z` passes 506 backend tests and 14/15 checks, but
notification timing and session-recovery browser tests fail. Preserve its evidence.
## Requirements
Keep real refresh behavior and notification assertions. Avoid rejection of bootstrap traffic
before the intended test action. Bound guardrail read queries while preserving scoped statistics.
## Non-goals
Arbitrary timeout increases, lower browser concurrency, weaker safety/permission checks.
## Acceptance Criteria
Populated catalog reads stay within six queries with exact counts/recent ordering and no
foreign results. Full browser suite passes under existing concurrency/timeouts; lint/build pass.
## Plan
1. Inspect failed traces and request timing; reproduce query amplification.
2. Arm session rejection from Refresh's account request; aggregate catalog statistics and
   window recent failures in a focused module, shrinking the existing service.
3. Run regression and full pipeline; inspect logs and document evidence without erasing failures.
## Verification
Query-count regression, guardrail/API tests, existing 26 Chromium checks and full local runner.
## Risks
SQL aggregation must retain zero-result defaults, ordering, search and workspace predicates.
Keep test-trigger changes separate from application latency claims.
## Progress
2026-09-08 full pipeline reproduced two browser failures. The catalog reproduction measured
150 queries. Statistics/failures moved to guardrail_catalog_stats.py; service shrank to 389
lines with a lowered baseline. The session test rejects document requests only after Refresh
starts its account read. Notification assertions/timeouts are unchanged.
## Decisions
Fix query amplification instead of weakening latency-sensitive assertions. One implementation owner.
## Findings
First reproduction fixtures used duplicate workspace names and omitted graph status; corrected
before measuring queries. All failed logs remain in `.artifacts/refresh-reliability/`.
## Final Result
Completed 2026-09-08. Final full pipeline passes all 15 gates: 507 backend tests, 26 browser
checks at unchanged concurrency/timeouts, 19 tooling tests, lint/build/types, migration and
dependency audit. Runtime: 2,519 HTTP outcomes, no server/error outcomes. Guardrail median
was 214.04 ms versus 1,170.31 ms in the earlier run; this is not a latency SLA.
Failed runs and fixture corrections remain preserved. See
[verification](../../testing.md#complete-regression-and-refresh-reliability).
