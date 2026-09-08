# Make evaluation metric claims match their evidence

## Goal
Stop reporting source-reference presence as factual groundedness and enforce all expected sources.
## Context
The current groundedness score is true whenever any citation exists, even for a wrong answer;
expected_sources also passes when only one of multiple required sources matches.
## Requirements
New runs emit citation_presence_rate from actual stored citations, not a grounding claim.
Keep old stored metrics unchanged and label them as a legacy proxy. All expected sources must match.
## Non-goals
Inventing an entailment heuristic, paid model judging or silently rewriting historical scores.
## Acceptance Criteria
A cited wrong answer receives no factual-grounding pass; required facts still fail via explicit
case constraints. Partial expected-source coverage fails. Correct review cases without citations
can pass their case checks while citation presence remains zero. UI labels distinguish old/new data.
## Plan
Update runner scoring and metric aggregation; extract frontend metric naming/ordering into a small
module to avoid growing AppShell. Add scoring/aggregation and browser-label regressions.
## Verification
Run evaluation/provider tests, frontend build, browser journeys, lint and structural/doc gates.
Inspect new response metrics and retain historical metric records.
## Risks
Case pass rate means configured checks passed, not semantic truth. Factual-support assessment
requires a validated rubric or human-reviewed labels and remains unimplemented.
## Progress
2026-09-07: inspected scoring, aggregation and UI labels; identified the false grounding implication.
Implementation is present: three regressions fail against the old image; 25 affected tests,
frontend build and three browser journeys pass. Evidence is in
`.artifacts/20260907-metric-contract/`. Backend lint fails E501 at evaluation_metrics.py:31
(102 characters, maximum 100). The user's documentation-only pass preserves application edits
and records this remaining check rather than closing the implementation plan.
## Decisions
2026-09-07: resumed application work under the full production goal, wrapped the overlong line,
and verified `ruff check app tests` passes; evidence: `lint-final.log` in the same artifact folder.
Prefer an honest measured name to a replacement heuristic presented as factual verification.
Keep legacy data identifiable and avoid comparing differently named metrics as equivalent.
## Findings
Final full backend regression passed 234 tests in 92.16 seconds, with one Starlette/httpx
deprecation warning; see `backend-final.log`. This supplements the focused and browser evidence.
The existing grounding calculation duplicates citation presence and waives even that on review cases.
## Final Result
Completed: the measured citation contract, required-source checks and UI labels are verified by
25 affected tests, frontend build, three browser journeys and final passing lint. Historical
scores remain untouched. Factual-support assessment remains open in the production plan.
