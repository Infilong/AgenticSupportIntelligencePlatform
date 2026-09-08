# Multilingual policy evidence
## Goal
Remove invented graph mock policies and verify the live EN/JA/ZH support journey.
## Context
The saved API journey fails 3/3 when seven-day sources produce canned 30-day answers.
The user resumed the full implementation objective after the documentation-only audit.
## Requirements
Mock responses quote bounded supplied evidence with exact citations and explicit simulation
labels. Preserve real-provider dispatch, workspace authorization, budget accounting and traces.
## Non-goals
Claiming semantic retrieval, real-model quality, or complete browser coverage from HTTP tests.
## Acceptance Criteria
Different policy facts survive in EN/JA/ZH without invented exceptions. Excerpts are bounded;
missing evidence never produces policy claims. Relevant backend and live workflow tests pass.
## Plan
1. Extract mock response construction from the oversized graph; lower its size baseline.
2. Add multilingual fact/citation/empty/length regressions; preserve source conditions.
3. Run backend checks, rebuild the isolated API and rerun the live journey; diagnose failures.
## Verification
Use Docker backend pytest/Ruff and the retained Playwright HTTP journey. Preserve logs under
`.artifacts/20260907-multilingual-workflow/`; review actual evidence and all changed files.
## Risks
Longer honest excerpts affect token budgets. Mocks cannot infer policy applicability. Source
excerpts remain untrusted data; exact citations alone do not establish factual entailment.
## Progress
2026-09-07: verified canned strings and saved failure; extracted bounded mock source excerpts.
Focused 37 and full 284 backend tests pass. Three multilingual HTTP journeys and three existing
browser regressions pass; lint, build, documentation and source-size gates pass. Graph shrank
from 824 to 761 lines; the legacy exception baseline was lowered.
## Decisions
One small helper owns deterministic mock text; graph remains the orchestration owner.
## Findings
The prior Chinese test expected a canned paraphrase that omitted the source's account condition.
## Final Result
Completed 2026-09-07. The canned-policy defect is repaired with explicit mock labeling, bounded
source excerpts and exact citations. Live HTTP acceptance passes in all three languages.
See [testing](../../testing.md#multilingual-policy-repair-verification) for exact evidence and
retained fixture/lint failures. Full multilingual browser and real AI quality remain open.
