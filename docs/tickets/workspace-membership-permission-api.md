# Workspace Membership Permission API

## Goal
Stop inferring workspace role and owner-only capabilities only in the frontend. Expose a backend-supported v1 permission payload so the shell and resource controls can show truthful role and permission state.

## Context
The active platform goal requires users to understand current workspace, current role, available permissions, and restricted actions. The previous shell pass displayed role by comparing `workspace.created_by_user_id` with the current user, which was useful but not authoritative enough for a professional platform.

## Requirements
- Add a workspace-scoped membership endpoint for the current authenticated user.
- Return role and explicit permissions from backend-owned membership data.
- Preserve workspace isolation: non-members receive the same not-found behavior as other workspace routes.
- Keep the v1 role model honest: `owner` and `member` only.
- Wire the frontend shell and owner-only resource controls to the backend permission payload.
- Add tests for owner, member, and non-member behavior.

## Non-goals
- No custom role editor.
- No admin member-management page.
- No migration or new role enum values.
- No claim that full RBAC/ABAC is implemented.

## Implementation Record
Backend:
- Added `WorkspaceMembershipResponse`.
- Added `permissions_for_role()` with truthful v1 owner/member permissions.
- Added `GET /api/v1/workspaces/{workspace_id}/membership`.
- Added tests proving owner permissions, member restrictions, and cross-workspace denial.

Frontend:
- Added `WorkspaceMembership` state loaded with workspace data.
- Replaced client-only owner inference with backend `can_manage_resources`.
- Displayed role, permission summary, and compact permission chips in the sidebar.
- Kept collapsed sidebar clean by hiding detailed permission text in compact mode.

## Validation
Run from repository root:

```bash
cd backend
uv run ruff check .
uv run pytest -s tests/test_auth_workspace.py tests/test_resource_folders.py

cd ../frontend
npm run test
npm run build
```

## Human Review Checklist
- Confirm the sidebar role is loaded from the backend membership endpoint.
- Confirm owner users see destructive/folder controls enabled.
- Confirm member users see controls disabled and no delete/resource-folder permissions.
- Confirm non-members cannot query membership for another workspace.
- Confirm permission chips are useful but not visually noisy.

## Known Limitations
- The role model still has only `owner` and `member`.
- Member permissions reflect what the current backend allows today; future tickets should tighten route-level permissions by product role.
- The UI still does not hide whole nav groups by role because backend read access is currently broad for members.
