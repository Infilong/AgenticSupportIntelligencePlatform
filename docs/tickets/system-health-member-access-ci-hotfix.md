# System Health Member Access CI Hotfix

## Goal
Fix the GitHub Actions backend failure where `WorkspaceRole.member` received `403 Forbidden` from `GET /api/v1/workspaces/{workspace_id}/system-health`.

## Context
The system health route correctly uses `require_workspace_permission("system:read")`. The failing test expects ordinary workspace members to read operational readiness for their workspace, while unrelated users must still receive `workspace_not_found`.

## Decision
Add `system:read` to the member role preset. This keeps the route permission-based and avoids weakening the endpoint dependency. Viewer and reviewer roles remain unchanged.

## Non-goals
- Do not redesign RBAC.
- Do not broaden non-member access.
- Do not make system health public.
- Do not add write/manage permissions to members.

## Test Plan
- `uv run pytest -s -q tests/test_system_health.py tests/test_auth_workspace.py`
- `uv run ruff check app/services/workspace_service.py tests/test_system_health.py tests/test_auth_workspace.py`
- `uv run pytest -s -q`

## Human Review Checklist
- Confirm the endpoint still requires authentication and workspace membership.
- Confirm non-members still receive `workspace_not_found`.
- Confirm only read-only system health access was added to members.

## Interview Notes
This is an example of keeping authorization centralized: endpoints depend on named permissions, while role presets decide who receives those permissions. The fix updates the role preset instead of bypassing the dependency.
