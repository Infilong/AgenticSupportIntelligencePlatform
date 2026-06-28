# Browser Smoke Test Harness

## Goal
Add repeatable browser-level smoke coverage for the frontend stability issues found during manual review: folder input focus, Human Review queue clarity, and review editor typing.

## Changes
- Added `@playwright/test` as a frontend dev dependency.
- Added `frontend/playwright.config.ts`.
- Added `frontend/tests/e2e/review-ux-smoke.spec.ts`.
- Added `npm run test:e2e` and `make frontend-e2e`.
- Added `make frontend-e2e-docker` so WSL can run Chromium through the official Playwright container without host browser libraries.
- Added Playwright generated artifact ignores for `frontend/test-results/` and `frontend/playwright-report/`.

## Smoke Test Coverage
The smoke test prepares data through the real backend API and then exercises the real browser UI:
1. Registers a fresh user.
2. Logs in and creates a workspace.
3. Creates an agent.
4. Runs a prompt-injection scenario to create a pending human review.
5. Opens the app with the returned JWT in browser local storage.
6. Uploads a real knowledge document through the backend API.
7. Verifies the Knowledge document library exposes move/delete controls for the uploaded document.
8. Verifies Knowledge folder input accepts multi-character typing and keeps focus.
9. Opens Human Review.
10. Verifies a pending review appears in the compact queue.
11. Types into Human-approved answer and Reviewer note fields and checks values/focus.

## Validation
- `cd frontend && npm run typecheck` -> passed.
- `cd frontend && npm run build` -> passed.
- `cd frontend && npx playwright install chromium` -> completed.
- Host-run `cd frontend && npm run test:e2e -- --project=chromium` -> blocked by missing WSL system library: `libnspr4.so`.
- Host-run `cd frontend && npx playwright install-deps chromium` -> blocked because WSL requires a sudo password.
- Docker-run `make frontend-e2e-docker` -> passed after rebuilding the frontend container.

## WSL E2E Command
With Docker services running:

```bash
cd /home/infilong/project/AgenticSupportIntelligencePlatform
make frontend-e2e-docker
```

The host `make frontend-e2e` target is still useful on machines with local Playwright browser dependencies installed. In this WSL environment, prefer the Docker target.

## Human Review Checklist
- In this WSL project, run `make frontend-e2e-docker` with Docker services running.
- If the test fails on selectors, inspect whether UI labels changed or behavior regressed.
- Do not weaken focus assertions; they exist to prevent the exact one-character focus-loss regression.

## Interview Note
This shows professional engineering discipline: a user-reported UX bug was converted into browser-level regression coverage using real API setup, not just TypeScript checks or manual confidence.
