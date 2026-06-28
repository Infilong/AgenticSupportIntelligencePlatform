# Permission Aware Secondary Shortcuts

## Goal
Make secondary shortcut buttons inside Settings and Agent panels respect the same tab permissions as the sidebar and dashboard.

## Context
After role-scoped backend reads and permission-aware dashboard shortcuts, several inner panels still showed direct navigation buttons to admin or developer pages. `goToTab` blocked them, but visible blocked shortcuts made restricted roles feel confusing.

## Requirements
- Add a reusable frontend shortcut helper for pure tab-navigation buttons.
- Hide Settings map entries when the target tab is not available to the current role.
- Hide Agent panel links to Models, Evaluations, Costs, or Traces when unavailable.
- Keep owner/developer behavior unchanged.

## Verification
- `cd frontend && npm run build` passed.
- `docker compose up -d --build frontend` rebuilt the running frontend; it also recreated API, so `/health` was checked before rerunning browser tests.
- `make frontend-e2e-docker` passed after API readiness: 2 Chromium tests passed.
