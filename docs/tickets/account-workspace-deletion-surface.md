# Account Workspace Deletion Surface

## Goal
Expose workspace deletion from the Account/workspace management page when the user has workspace management permission.

## Context
The backend already supports owner-only workspace deletion with exact-name confirmation, audit logging, and soft delete through `deleted_at`. Settings also has a danger zone, but Account is now the canonical workspace management entry point, so deletion should be visible there too.

## Common Policy Used
This project follows a common SaaS workspace lifecycle policy:
- normal user delete is a soft delete;
- the workspace disappears from normal user lists immediately;
- audit logs, AI run ledger, traces, cost records, and operational evidence are retained for governance, debugging, and abuse investigation;
- permanent purge is a separate administrative/data-retention process, not a normal workspace-management click.

## Changes
- Added an Account-page workspace deletion panel.
- Required exact workspace name confirmation before enabling Delete.
- Disabled deletion when the user lacks `can_manage_workspace` permission.
- Reused the existing backend delete endpoint and AppShell deletion handler.
- Kept backend behavior unchanged because owner-only soft delete already exists and is covered by tests.

## Validation
- `npm --prefix frontend run typecheck` passed.
- `npm --prefix frontend run build` passed.
- `cd backend && uv run pytest -q tests/test_auth_workspace.py -k "workspace_delete or membership_endpoint_returns_owner_permissions"` passed.

## Manual Review Checklist
- Open Account.
- Select a workspace where the user is owner.
- Confirm the Workspace deletion panel appears.
- Type the exact workspace name and confirm the Delete button enables.
- Delete and confirm the workspace disappears from the workspace list.
- Confirm users without workspace management permission see the panel as restricted.
