# Workspace Lifecycle Management

## Goal
Add GitHub-style workspace management so users can understand and control workspace lifecycle, permissions, and destructive actions from the app instead of only creating/selecting workspaces.

## Context
The Account page already supported workspace creation and selection, but the product had no visible controls for archive, restore, leave, delete, or backend permission inspection. The backend also needed explicit lifecycle state so deleted workspaces stop appearing without hard-deleting workspace-owned records.

## Requirements
- Prevent duplicate workspace names in each user active workspace list.
- Add owner-only archive and restore actions.
- Make archived workspaces readable but block write-level workspace permission dependencies.
- Add owner-only delete with exact workspace-name confirmation.
- Treat delete as soft delete so audit/resource history is not physically removed during this portfolio stage.
- Add self-leave action with a last-owner guard.
- Expose a backend permission matrix endpoint for the current workspace.
- Show archived workspace state in Account and Settings UI.
- Keep destructive controls separated in a danger zone.

## Non-goals
- Full GitHub organization billing, invitation, transfer, or enterprise SSO behavior.
- Hard-delete cascades for every workspace-owned entity.
- Complex custom role editor.
- Large frontend architecture refactor of the existing AppShell state container.

## Design Summary
Backend:
- Added archived_at and deleted_at to Workspace with Alembic migration 0024_workspace_lifecycle.
- Workspace list/get filters out soft-deleted workspaces.
- Workspace name conflict checks ignore soft-deleted workspaces but still include archived workspaces.
- Added lifecycle routes: archive, restore, leave, delete, and permission-matrix.
- Added archived-workspace write blocking in require_workspace_permission.
- Added route-level archived guards for owner-only workspace mutations such as rename and member management.

Frontend:
- Account page shows archived workspace counts and badges.
- Settings page now contains workspace identity, settings shortcuts, backend permission matrix, and danger zone.
- AppShell wires the lifecycle API calls and clears stale delete confirmation when workspace selection changes.
- Settings-specific styles live in frontend/src/settings-page.css rather than expanding the global stylesheet.

## Tests
- Added backend tests for permission matrix scoping, archive/restore read-only behavior, delete confirmation/ownership, and self-leave/last-owner protection.
- Ran focused and full backend tests.
- Ran frontend production build.

## Validation
- cd backend && uv run pytest -s tests/test_auth_workspace.py -q -> 29 passed, 1 warning.
- cd backend && uv run pytest -s -q -> 182 passed, 1 warning.
- cd backend && uv run ruff check . -> All checks passed.
- cd frontend && npm run build -> passed.

## Risks And Follow-ups
- Existing frontend/src/app/AppShell.tsx is still a large state container; this ticket kept wiring minimal but does not solve that architectural debt.
- Existing backend workspace API/service files exceed the preferred 300-line guidance. Future workspace features should split lifecycle/member behavior into smaller route/service modules.
- Soft delete is intentional for now. A production hard-delete path would need retention policy, export, background cleanup, and owner confirmation UX.
- Browser visual QA should be repeated after container rebuild because this ticket changes important settings controls.

## Human Review Checklist
- Confirm archive blocks resource writes, workspace rename, and member mutations but still allows read-only inspection and restore.
- Confirm delete requires exact workspace name and removes the workspace from the user list.
- Confirm non-owners cannot archive, restore, or delete.
- Confirm leaving as the last owner fails.
- Confirm Settings page danger zone is understandable and not too prominent for normal workflows.

## Interview Notes
- Explain why archive and soft delete are separate states.
- Explain why permission checks stay server-side and the frontend only displays backend-derived permission data.
- Explain why archived workspaces are read-only rather than hidden immediately.
- Explain the tradeoff of soft deletion in a local portfolio system versus a production retention/deletion pipeline.
