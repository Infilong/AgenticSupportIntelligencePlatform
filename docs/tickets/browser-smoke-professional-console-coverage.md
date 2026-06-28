# Browser Smoke Professional Console Coverage

## Goal
Extend browser-level smoke coverage so professional-console UX regressions are caught in the surfaces most tied to the active product objective.

## Context
Build and typecheck prove the React app compiles, but they do not prove that the interface remains intuitive, stable, and usable in a browser. Prior manual review found focus loss, confusing review UI, and growing resource lists. The existing Playwright test already provisions real backend data and exercises folders, review, traces, tools, evaluations, and guardrails.

## Requirements
- Verify the collapsible sidebar can hide and show without losing navigation usability.
- Verify review queue search keeps focus and still exposes the pending review case.
- Verify Usage & costs has a searchable investigation surface.
- Verify Audit has a searchable operations timeline.
- Keep the smoke path backed by real API-created workspace data.

## Non-goals
- No screenshot pixel review in this ticket.
- No new backend API behavior.
- No broad E2E suite split.
- Keep the broad smoke timeout realistic enough for API setup plus full browser navigation.

## Implementation
- Extended `frontend/tests/e2e/review-ux-smoke.spec.ts`.
- Forces the sidebar into expanded state at test startup, then verifies collapse and expand behavior.
- Adds browser checks for cost investigation search, audit search, and review queue search/focus behavior.
- Names compact folder move controls as accessible groups so browser tests and assistive tech can identify them.

## Verification
- `cd frontend && npm run build` passed.
- `make frontend-e2e-docker` passed with the real Docker API/frontend/PostgreSQL stack.

- `cd backend && uv run pytest -s tests/test_agents.py tests/test_resource_folders.py` passed: 28 passed, 1 warning.

## Risks
- The smoke test is intentionally broad and can fail when page copy changes. This is acceptable for now because the app is a portfolio product where visible IA/copy are part of the product contract.
- Full visual QA still needs screenshot review or a dedicated `/qa` pass.

## Interview Notes
Explain this as closing the gap between compiled UI and usable product. A professional AI platform should verify critical browser workflows: permission-aware navigation, foldered resources, human review typing, trace inspection, and operations search.
