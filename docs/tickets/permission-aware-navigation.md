# Permission-Aware Navigation And Page Gating

## Goal
Make navigation reflect backend membership permissions so users only see product areas they can access, and blocked deep links/shortcuts fail clearly instead of opening hidden admin surfaces.

## Context
The active product goal requires the sidebar to show only features the current user has permission to access. The app already loads `WorkspaceMembership` from the backend and displays permission chips, but the sidebar still renders every tab for every workspace member.

## Requirements
- Add page-level read permissions to the backend membership payload.
- Keep owner-only write/admin permissions for destructive and configuration changes.
- Add frontend tab metadata describing required permissions.
- Filter sidebar sections from accessible tabs only.
- Guard tab changes from dashboard cards, settings shortcuts, and deep state changes.
- If a tab becomes unavailable after workspace/role changes, route back to Dashboard.
- Show a restricted-access empty state if a hidden tab is somehow active.
- Keep collapsed sidebar behavior stable.

## Non-goals
- Do not add enterprise custom roles in this ticket.
- Do not change backend route authorization beyond truthful permission payload naming.
- Do not hide read-only pages from members when backend still allows read access.

## Test Plan
- Backend membership tests prove owner/member permission payloads include page-level read permissions and owner-only write permissions remain owner-only.
- Frontend typecheck/build.
- Browser smoke verifies existing focus/folder/review path remains stable.

## Acceptance Criteria
- Sidebar is generated from accessible tabs, not the full static tab list.
- UI shortcuts use the same guarded navigation path as the sidebar.
- Members do not see pages unless their backend membership payload includes the required page permission.
- Admin write controls remain disabled without owner permissions.

## Implementation Notes
- Added explicit page-level read permissions to `MEMBER_PERMISSIONS` so the membership API can truthfully drive navigation visibility.
- Corrected `search_documents` tool metadata from stale `knowledge:write` to read-only `knowledge:read`.
- Kept destructive/configuration permissions owner-only: resource cleanup, prompt/model writes, tool/guardrail configuration, and budget management.
- Added frontend tab permission metadata and builds sidebar sections from accessible tabs only.
- Routed dashboard cards, settings map links, attention items, trace/review shortcuts, and sidebar clicks through one guarded `goToTab` path.
- Added a restricted-access empty state and a fallback to Dashboard when the active tab becomes unavailable after workspace or role changes.

## Verification
- `cd backend && uv run ruff check app/services/workspace_service.py tests/test_auth_workspace.py`
- `cd backend && uv run pytest -s -q tests/test_auth_workspace.py` - 19 passed
- `cd frontend && npm test -- --run`
- `cd frontend && npm run build`
- `cd backend && uv run pytest -s -q` - 136 passed
- `make frontend-e2e-docker` - 1 passed

## Follow-up Requirements Captured
- Audit every user-uploaded resource path and ensure users with sufficient permission can delete/archive what they upload or own.
- Replace unbounded flat frontend fields/lists for growing file/resource names with foldered or grouped resource management views.

