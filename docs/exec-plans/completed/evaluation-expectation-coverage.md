# Evaluation expectation coverage
## Goal
Report tool/guardrail expectation coverage only for cases that actually test those behaviors.
## Context
Empty expectation lists receive vacuous per-case passes and currently inflate aggregate quality.
Nine untested cases can mask one failed expected behavior as a 90 percent result.
## Requirements
Persist expected tool/guardrail lists with new result scores. Aggregate only nonempty expectations;
omit unmeasured metrics. Use new metric names to distinguish historical all-case denominators.
Keep case pass semantics, stored historical results, workspace access and provider accounting intact.
## Non-goals
General semantic grading, changing route/language/citation metrics, rewriting historical runs,
or claiming subset matching proves all tool behavior correct.
## Acceptance Criteria
An untested run has no expectation-coverage rate. One tested failure plus untested cases scores
zero, with independent mode/language grouping. Real evaluated successes retain full coverage.
Historical metric names remain readable and are labeled as legacy in the UI.
## Plan
1. Reproduce inflated/untested metrics with focused scoring regressions.
2. Extract case scoring into a cohesive module, persist expected lists, and correct aggregation.
3. Update metric labels/contracts; verify API, comparison, frontend and full affected regressions.
## Verification
Preserve failed and corrected evidence under `.artifacts/evaluation-coverage-*`.
Run Ruff, relevant evaluation tests, frontend build/browser acceptance, docs/source checks.
## Risks
Old and new rates use different denominators and must not be silently compared. Omission means
unmeasured, not failure or perfect success. Nonempty expected lists test inclusion, not exclusion.
## Progress
2026-09-08: inspected scoring, aggregate persistence and UI rendering; no schema change needed.
Reproduction: four failures and one pass in `.artifacts/evaluation-coverage-before.log`.
Extracted scoring from the evaluator (479 to 420 lines); new results store expected lists and
null untested match scores. Aggregates omit unmeasured rates and use distinct metric keys;
UI labels retain legacy provenance. Ruff and 49 focused tests pass in
`.artifacts/evaluation-coverage-verified.log`. Multilingual browser cases now test measured
tool expectations and absence of untested guardrail rates. Full pipeline completed successfully
in `.artifacts/20260908T000709309Z/`: 17/17 gates, 639 backend tests and 27 browser tests
in each deployment mode. Runtime review found no server/error outcomes among 2,521 main-stack
and 1,821 compiled-image HTTP outcomes. See [verification details](../../testing.md#evaluation-expectation-coverage-and-full-regression).
## Decisions
Use new metric keys and retain historical records rather than reinterpret old evidence.
## Findings
Previous optional-check defaults were 1.0, including cases without expectations. New null
scores and expectation metadata distinguish untested cases from measured successes.
Separate follow-up: system evaluation prompt-token aggregation reads graph step total tokens;
case max_prompt_tokens is stored but not checked by case scoring. These require focused repair.
## Final Result
Complete for optional expectation coverage. Historical metrics remain readable under their
original names; new rates measure only cases with nonempty expectations. Subset matching does
not establish semantic correctness or reject unexpected extra tool calls. Broader production
readiness remains open.
