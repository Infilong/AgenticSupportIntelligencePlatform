# Workspace Settings Admin

## Goal
Add a serious Settings area with backend-supported workspace identity management instead of leaving settings as scattered admin pages.

## Context
The app already had Members, Models, Prompts, Audit, and System Health pages, but no dedicated workspace settings page and no backend route for updating workspace identity. The active goal requires serious settings pages, permission-aware controls, and backend-supported product logic.

## Requirements
- Add owner-gated workspace settings update API.
- Record workspace identity changes in the audit log.
- Keep non-members unable to discover or edit another workspace.
- Add a Settings navigation group/tab.
- Show role-aware Settings UI: owners can rename, members can inspect but cannot edit.
- Route advanced settings to their existing backend-supported pages instead of creating fake controls.

## Non-goals
- No browser-stored API keys.
- No fake global budget/rate-limit settings.
- No new enterprise RBAC model beyond current owner/member roles.
- No workspace deletion yet.

## Design Plan
- Add `WorkspaceUpdateRequest` schema.
- Add `WorkspaceService.update_workspace_name`.
- Add `PATCH /api/v1/workspaces/{workspace_id}` using `require_workspace_owner`.
- Add backend tests for owner update, member denial, blank validation, and workspace isolation.
- Add frontend Settings tab with workspace identity form and settings map links.

## Test Plan
- Run focused workspace backend tests.
- Run frontend typecheck/build.
- Run full backend tests and lint.
- Run `git diff --check`.
- Rebuild Docker API/frontend.
- Live smoke test workspace rename through the running API.

## Acceptance Criteria
- Owners can rename a workspace.
- Members cannot rename a workspace.
- Non-members get workspace-not-found.
- Blank names are rejected.
- Settings page makes configurable vs planned controls clear.
- Workspace rename appears in audit logs.

## Risks
- Current v1 role model is still owner/member only; the Settings page must not imply full enterprise RBAC.
- API keys remain environment-level, which is appropriate for local-first v1 but should be documented as a production extension.

## Human Review Checklist
- Confirm Settings is discoverable from the left navigation.
- Confirm the workspace name change updates the sidebar/topbar after saving.
- Confirm non-owner users see disabled controls and clear explanations.
- Confirm settings map links go to real admin pages.

## Interview Notes
This ticket shows product integrity: settings are not just UI decoration. The workspace identity change is backend-authorized, workspace-scoped, validated, audited, and exposed through a role-aware admin console.

## Validation Results
- `cd backend && uv run ruff check app/api/v1/workspaces.py app/schemas/workspace.py app/services/workspace_service.py tests/test_auth_workspace.py`: passed.
- `cd backend && uv run pytest tests/test_auth_workspace.py -q -s`: 19 passed, 1 Starlette/httpx deprecation warning.
- `cd frontend && npm run test -- --run`: passed TypeScript check.
- `cd frontend && npm run build`: passed.
- `cd backend && uv run ruff check .`: passed.
- `cd backend && uv run pytest -q -s`: 123 passed, 1 Starlette/httpx deprecation warning.
- `git diff --check`: passed.
- `docker compose up -d --build api frontend`: rebuilt and restarted services.
- Live smoke `PATCH /api/v1/workspaces/{workspace_id}`: renamed a workspace and confirmed the detail endpoint returned the new name.
- Live smoke `GET http://127.0.0.1:5173`: returned frontend HTML.
