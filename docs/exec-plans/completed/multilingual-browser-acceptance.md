# Multilingual browser acceptance
## Goal
Verify the complete EN/JA/ZH support journey through the application's visible controls.
## Context
Three multilingual HTTP journeys pass, but existing browser regressions seed data through APIs.
## Requirements
Register/login, workspace creation, dataset import, knowledge upload, agent creation/run,
trace inspection, review resolution, evaluation and costs must work through browser controls.
## Non-goals
Semantic embedding quality, real-provider billing, complete permission coverage or release certification.
## Acceptance Criteria
Three isolated language journeys pass with mock providers; visible answers preserve source
facts and citations, trace navigation works, unsafe runs can be rejected, quality/cost views load.
## Plan
1. Inspect accessible controls and existing browser test conventions.
2. Add a focused acceptance specification without API setup mutations or injected auth tokens.
3. Run, inspect failures, repair actual application defects or incorrect test assumptions.
4. Verify and preserve evidence; update quality status with precise coverage limits.
## Verification
Playwright Chromium on the isolated local stack. Capture logs/screenshots/traces under
`.artifacts/20260907-browser-acceptance/`. Network observation verifies UI-persisted outcomes.
## Risks
Async state transitions and ambiguous selectors can expose fixture errors. Preserve failures;
do not replace browser actions with API shortcuts. Mocks cannot establish real AI quality.
## Progress
2026-09-07: added three UI-only journeys. Reproduced/fixed the folder-picker hook-count crash
and late run-refresh navigation overriding review. Nine Playwright tests pass in 26.4 seconds;
frontend build, documentation/source-size checks and diff whitespace pass.
## Decisions
One test file owns acceptance flow; tightly coupled UI changes remain under the primary owner.
## Findings
Prior tests bypassed onboarding/import/upload/run actions through seeded API state. New journeys
exposed two application defects. Selector failures and one unreproduced fetch exception remain
in the evidence logs; final journeys assert no browser exceptions.
## Final Result
Completed 2026-09-07. All three mock-provider language journeys work through browser controls.
See [testing](../../testing.md#multilingual-browser-acceptance) for exact scope and failed/successful
evidence. Full permission denial, semantic AI quality and production recovery remain open.
