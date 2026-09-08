# Evaluation comparison provenance
## Goal
Prevent historical accounting/scoring changes from appearing as quality or efficiency gains.
## Context
Comparisons currently subtract same-name metrics without knowing their scoring contract.
Recent optional expectations, model-ledger accounting and case-limit acceptance changed it.
## Requirements
Stamp new scores with a durable contract identifier. Compare only matching known contracts
within each mode/language group; mixed or unknown groups retain values but no delta/direction
of improvement. Preserve workspace checks and historical records.
## Non-goals
Historical backfill, proving identical case sets or provider configurations, semantic grading.
## Acceptance Criteria
API comparisons mark unknown/different/mixed contracts incomparable with null deltas; matching
contracts retain existing comparisons. No incompatible rows count as improvements/regressions.
## Plan
1. Reproduce current historical comparison behavior with API tests.
2. Extract comparison ownership from the oversized runner; stamp scoring output.
3. Verify regression boundaries and document compatibility/remaining limits.
## Verification
Ruff, evaluation tests, source-size/docs/whitespace checks. Keep evidence in .artifacts.
## Risks
Legacy-to-legacy comparisons also lack reliable provenance. Version equality alone cannot
prove equivalent datasets, prompts or model configuration. Do not claim it can.
## Progress
2026-09-08: inspected persisted scores, comparison API and existing generic direction badge.
Added reproduction tests; no database migration needed for scores_json metadata.
Two API failures reproduced in `.artifacts/comparison-provenance-before.log`. Extracted
comparison ownership; runner reduced from 420 to 349 lines. Ruff and all 98 evaluation tests
pass in `.artifacts/comparison-provenance-acceptance.log` (71.06s, PostgreSQL enabled).
Documentation, source-size and whitespace checks pass. No frontend change or browser rerun.
## Decisions
Use an explicit contract marker rather than infer provenance from timestamps or metric names.
## Findings
Existing UI renders string directions and null deltas; no application shell growth needed.
## Final Result
Complete for contract compatibility: unknown/mixed/different contracts are incomparable,
matching contracts retain existing behavior, and workspace-denial regressions pass. Existing
generic UI rendering was inspected, not revalidated in a browser this increment. Dataset,
prompt and model equivalence remain separate experimental requirements.
