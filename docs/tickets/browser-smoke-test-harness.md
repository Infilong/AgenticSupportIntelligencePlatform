# Browser Smoke Test Harness

## Goal
Add repeatable browser-level smoke coverage for the frontend stability issues found during manual review: folder input focus, Human Review queue clarity, and review editor typing.

## Changes
- Added `@playwright/test` as a frontend dev dependency.
- Added `frontend/playwright.config.ts`.
- Added `frontend/tests/e2e/review-ux-smoke.spec.ts`.
- Added `npm run test:e2e` and `make frontend-e2e`.
- Added Playwright generated artifact ignores for `frontend/test-results/` and `frontend/playwright-report/`.

## Smoke Test Coverage
The smoke test prepares data through the real backend API and then exercises the real browser UI:
1. Registers a fresh user.
2. Logs in and creates a workspace.
3. Creates an agent.
4. Runs a prompt-injection scenario to create a pending human review.
5. Opens the app with the returned JWT in browser local storage.
6. Verifies Knowledge folder input accepts multi-character typing and keeps focus.
7. Opens Human Review.
8. Verifies a pending review appears in the compact queue.
9. Types into Human-approved answer and Reviewer note fields and checks values/focus.

## Validation
- `cd frontend && npm run typecheck` -> passed.
- `cd frontend && npm run build` -> passed.
- `cd frontend && npx playwright install chromium` -> completed.
- `cd frontend && npm run test:e2e -- --project=chromium` -> blocked by missing WSL system library: `libnspr4.so`.
- `cd frontend && npx playwright install-deps chromium` -> blocked because WSL requires a sudo password.

## Required Local Setup To Run E2E
Run this once in WSL with sudo access:

```bash
cd /home/infilong/project/AgenticSupportIntelligencePlatform/frontend
sudo npx playwright install-deps chromium
npx playwright install chromium
```

Then, with Docker services running:

```bash
cd /home/infilong/project/AgenticSupportIntelligencePlatform
make frontend-e2e
```

## Human Review Checklist
- After installing WSL browser dependencies, run `make frontend-e2e`.
- If the test fails on selectors, inspect whether UI labels changed or behavior regressed.
- Do not weaken focus assertions; they exist to prevent the exact one-character focus-loss regression.

## Interview Note
This shows professional engineering discipline: a user-reported UX bug was converted into browser-level regression coverage using real API setup, not just TypeScript checks or manual confidence.
