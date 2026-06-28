# Role Aware Action Controls

## Goal
Make readable pages honest about which actions the current role can actually perform.

## Context
Backend permissions now correctly protect write/run/review actions, but several frontend panels still showed primary action controls to users who only had read access. That is confusing for reviewers and viewers and makes the app feel less professional.

## Requirements
- Agent create/configure controls require `agents:configure`.
- Agent execution controls require `agents:run`.
- Human review claim/release/resolve controls require `reviews:resolve`.
- Read-only users should still inspect allowed data and traces.
- Do not remove backend permission enforcement.

## Verification
- `cd frontend && npm run build` passed.
- `docker compose up -d --build frontend` rebuilt the running frontend for browser QA.
- `make frontend-e2e-docker` passed: 2 Chromium tests passed.
