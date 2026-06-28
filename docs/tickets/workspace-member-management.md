# Workspace Member Management

## Goal
Make workspace administration real instead of only showing the current user's membership. Owners should be able to see members, add registered users, change v1 roles, and remove non-self members through backend-enforced APIs and a professional Admin page.

## Context
The active product objective requires workspace settings, member management, role/permission visibility, and permission-aware UI. Before this ticket, the app exposed `GET /membership` for the current user, but it did not provide an owner-facing member management workflow.

## Requirements
- List workspace members from backend membership data.
- Add an existing registered user to a workspace by email.
- Support only honest v1 roles: `owner` and `member`.
- Allow owners to update another member's role.
- Allow owners to remove another member.
- Prevent self-removal and self-demotion for owners.
- Preserve at least one workspace owner.
- Deny member-management mutation to non-owners in the backend.
- Record audit logs for add, role update, and removal.
- Add frontend Admin navigation and a Members page wired to the real APIs.

## Non-goals
- No invitation emails.
- No unregistered-user invites.
- No custom enterprise RBAC or ABAC.
- No viewer/reviewer/developer role enum yet.
- No organization-wide user directory.

## Backend Changes
- Added workspace member service errors and lifecycle methods:
  - list members
  - add by registered email
  - update role
  - remove member
  - owner safety checks
- Added workspace member schemas:
  - `WorkspaceMemberResponse`
  - `WorkspaceMemberAddRequest`
  - `WorkspaceMemberRoleUpdateRequest`
- Added workspace routes:
  - `GET /api/v1/workspaces/{workspace_id}/members`
  - `POST /api/v1/workspaces/{workspace_id}/members`
  - `PATCH /api/v1/workspaces/{workspace_id}/members/{member_user_id}`
  - `DELETE /api/v1/workspaces/{workspace_id}/members/{member_user_id}`
- Added audit events:
  - `workspace_member.added`
  - `workspace_member.role_updated`
  - `workspace_member.removed`

## Frontend Changes
- Added Admin > Members navigation.
- Added member list, owner/member counts, permission chips, and current-user badge.
- Added owner-only controls for adding registered users, changing roles, and removing members.
- Added restricted-state copy for non-owners.
- Added wrapping card layout so long emails and permission names do not stretch the UI.

## Verification
- `cd backend && uv run ruff check app tests/test_auth_workspace.py`
- `cd backend && uv run pytest tests/test_auth_workspace.py -q -s`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm run build`

## Human Review Checklist
- Confirm Admin > Members appears in the left navigation.
- Register a second account, then add it from an owner workspace using its email.
- Confirm the second account can see the workspace after being added.
- Confirm owner-only actions are disabled or denied for member accounts.
- Confirm the Audit page records member add, role update, and removal.
- Confirm the UI wording does not claim full enterprise RBAC.

## Known Limitations
- V1 supports only `owner` and `member` roles.
- Users must register before they can be added to a workspace.
- There is no email invitation flow.
- There is no role-specific sidebar hiding yet because most member read access is still broad by backend design.
