# Permission Aware Overview Shortcuts

## Goal
Make the dashboard shortcuts match the role-scoped navigation and backend permissions. Users should not see prominent cards or shortcut buttons for product areas they cannot open.

## Context
The sidebar filters tabs by `requiredPermissions`, and `goToTab` blocks restricted navigation. The dashboard still rendered static shortcut cards for tools, prompts, models, audit, and other areas. That made reviewer/viewer roles confusing because the first screen advertised hidden/admin features.

## Requirements
- Render Overview operation buttons only for tabs the current role can open.
- Render dashboard resource/admin shortcut cards only for tabs the current role can open.
- Keep permanent informational cards for permissions and scale path.
- Add browser coverage for a restricted reviewer role.
- Do not change backend permissions in this ticket.

## Verification
- `cd frontend && npm run build` passed.
- `docker compose up -d --build api frontend` was required so the smoke suite used the latest backend role presets.
- `make frontend-e2e-docker` passed: 2 Chromium tests passed.

## Acceptance Criteria
- Reviewer dashboard does not show Tools, Prompts, Models, Audit, Data, Evaluations, or Guardrails shortcuts if those tabs are unavailable.
- Reviewer navigation still shows allowed pages such as Dashboard, My Tasks, Knowledge, Agents, Runs & traces, Human review, Usage & costs, and Settings.
- Owner/developer dashboard behavior remains intact.
