# UX-0A: App Shell Extraction Hardening (No Behavior Change)

## Goal
Reduce coupling in `frontend/src/app/AppShell.tsx` by extracting inline page rendering and orchestration logic into dedicated page components while preserving all existing behavior.

## Context
This ticket is the first active implementation step for `UX-0` in the frontend recovery plan. The backend is functionally complete for platform flows; the immediate risk is frontend architecture and maintainability.

## Scope
- **Do not** alter user-visible behavior, API contracts, or auth/permission semantics.
- Convert heavy in-`AppShell.tsx` sections into imports/calls to already existing page modules.
- Ensure `AppShell.tsx` focuses on composition, active-tab routing, and minimal shell-level state.
- Keep API calls, data mapping, mutation handlers, and error handling in domain page modules/hooks when practical.

## Requirements
- Build passes after each extraction batch.
- `frontend/src/app/AppShell.tsx` decreases in size substantially.
- No functional path changes for Overview/Tasks/Data/Knowledge/Agents/Runs/Reviews/Evaluations/Costs.
- No behavior changes for role filtering and permission checks.

## Design plan
1. Split the current AppShell responsibilities by section:
   - overview
   - tasks
   - datasets
   - knowledge
   - agents
   - tools
   - traces/runs
   - reviews
   - evaluations
   - costs
   - admin/system
2. For each section:
   - move render logic to the matching page module,
   - keep shell state wiring minimal,
   - avoid changing API calls unless necessary for extraction.
3. Introduce a shared `pageProps` object for common state and handlers only when it reduces duplication.
4. Preserve existing callbacks and data shape by shallow integration first.

## Files to change
- `frontend/src/app/AppShell.tsx`
- `frontend/src/pages/{OverviewPage.tsx,TasksPage.tsx,DatasetsPage.tsx,DocumentsPage.tsx,AgentsPage.tsx,ToolsPage.tsx,ReviewsPage.tsx,EvaluationsPage.tsx,CostsPage.tsx,SettingsPage.tsx,AuditPage.tsx}` *(create missing page files as needed)*
- `frontend/src/components` shared shell/panel primitives *if a safe split boundary is identified*
- `docs/tickets/ux-0a-appshell-extraction.md`

## Success criteria
- `npm run -C frontend build` passes.
- Manual smoke path remains intact (login → overview → one non-admin task → one trace path).
- No test expected to require API contract changes.

## Risks
- High chance of accidental prop mismatches and missing dependencies during first extraction.
- Risk of changing timing/errors if state dependencies are not preserved.
- Risk of route/visibility mismatch for role-based tabs.

## Human review checklist
- Confirm no new feature behavior was introduced.
- Confirm role/permission gating remains unchanged.
- Confirm `AppShell.tsx` no longer owns business logic for each page.
- Verify all existing actions still trigger and fail in the same cases.
