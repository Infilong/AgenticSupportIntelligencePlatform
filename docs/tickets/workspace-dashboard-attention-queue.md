# Workspace Dashboard Attention Queue

## Goal
Make the Overview dashboard task-oriented instead of mostly status-card oriented, using real workspace data to show what needs attention and what the current user can do.

## Context
The active product goal requires a professional operations console where users quickly understand workspace state, role, permissions, next action, failed/risky items, and relevant platform tools. The previous dashboard showed readiness and live operations but did not have a consolidated attention queue or a backend-backed permissions panel.

## Requirements
- Add a dashboard attention section backed by existing loaded API data.
- Do not invent fake alerts or placeholder metrics.
- Include actionable links to the relevant product area.
- Add a dashboard-level permissions panel using the workspace membership payload.
- Keep the layout professional, monochrome, and readable.

## Non-goals
- No new backend attention-query API in this ticket.
- No notification inbox or persistent task model.
- No first-class failed-run list API.
- No role-management UI.

## Implementation Record
- Added attention items derived from pending human reviews, failed document indexing, failing evaluation results, missing active model config, missing retrieval knowledge, loading permission state, and top model spend when available.
- Added click-through actions from attention items to Reviews, Knowledge, Evaluations, Models, Costs, or Overview.
- Added a My permissions dashboard panel backed by `WorkspaceMembership` data.
- Added dense neutral styling for attention items and permission summary grids.

## Validation
Run from repository root:

```bash
cd frontend
npm run test
npm run build
```

Then rebuild the local frontend:

```bash
docker compose up -d --build frontend
curl -sS -I http://127.0.0.1:5173
```

## Human Review Checklist
- Confirm the Overview page now answers what needs action, not only what exists.
- Confirm every attention item comes from real loaded state.
- Confirm empty state says no urgent tasks instead of showing fake alerts.
- Confirm permission panel matches the sidebar role and permission chips.
- Confirm click-through actions open the expected pages.

## Known Limitations
- This is still a client-assembled attention queue. A future backend task model should aggregate failed runs, guardrail blocks, evaluation regressions, and high-cost outliers more reliably.
- The dashboard only knows about evaluation failures when an evaluation detail is loaded in frontend state.
