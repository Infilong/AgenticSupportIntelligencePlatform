# Dockerized Browser Smoke Runner

## Goal
Make browser-level QA runnable in this WSL project without requiring host Chromium system packages or sudo access.

## Context
The frontend smoke test previously existed, but local Playwright Chromium failed in WSL because `libnspr4.so` was missing and `npx playwright install-deps chromium` required sudo. Docker is already part of the project workflow, so the official Playwright image is the lowest-friction runner.

## Changes
- Added `make frontend-e2e-docker`.
- The target cleans generated Playwright artifacts inside the frontend workspace.
- The target runs `mcr.microsoft.com/playwright:v1.61.1-noble` with host networking so browser JavaScript can reach `http://127.0.0.1:8000` and `http://127.0.0.1:5173`.
- The target runs as the WSL user for generated artifacts after cleanup.
- Added `allowedHosts: ["frontend"]` to Vite for Compose-network access when needed.

## Validation
- `make frontend-e2e-docker`: passed.
- Failure found before the pass: the running frontend container was stale because Compose copies source into the image. Rebuilding with `docker compose up -d --build frontend` fixed it.

## Human Review Checklist
- Prefer `make frontend-e2e-docker` for WSL browser QA.
- Rebuild frontend with `docker compose up -d --build frontend` after source edits because the Compose service does not mount local frontend source.
- Keep smoke tests backed by real API setup, not static mocked pages.

## Interview Notes
This is a practical QA infrastructure decision: browser regressions should be reproducible in the same Docker-first local environment used by the app, especially when WSL host dependencies are unreliable.
