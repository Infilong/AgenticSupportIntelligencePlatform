# Workspace Role Presets and Permission Gates

## Goal
Move the platform from a two-role owner/member model toward professional role-aware operations for owners, developers, reviewers, and viewers. The key requirement is backend enforcement, not only frontend hiding.

## Context
The active platform goal says users should understand their workspace role, available permissions, and restricted actions. Before this ticket, the app exposed a membership endpoint and permission chips, but `WorkspaceRole` only had `owner` and `member`. Many write or operate APIs accepted any workspace member, which made reviewer/viewer UX impossible to enforce honestly.

## Requirements
- Add role presets: `owner`, `developer`, `reviewer`, `viewer`, with legacy `member` preserved.
- Keep existing legacy `member` workspaces compatible.
- Add a reusable backend permission dependency that returns 403 with the required permission.
- Gate key write/operate routes by permission, not generic membership:
  - dataset import and labels: `data:write`
  - knowledge upload and reindex: `knowledge:write`
  - folder create/update/delete and resource moves: `resource_folders:manage`
  - agent create/update: `agents:configure`
  - agent run: `agents:run`
  - agent archive: `agents:delete`
  - human-review claim/release/resolve: `reviews:resolve`
  - evaluation run: `evaluations:run`
  - dataset/document/evaluation deletion/archive: `resources:delete`
- Update frontend role selector and permission-aware controls.
- Add tests proving distinct role permissions and denied/allowed backend actions.

## Non-Goals
- Do not build arbitrary custom enterprise RBAC.
- Do not change model, prompt, budget, guardrail-policy, or tool-config owner-only semantics in this ticket.
- Do not remove the legacy `member` role from existing data.

## Implementation
- Extended `WorkspaceRole` with `developer`, `reviewer`, and `viewer`.
- Added Alembic migration `0018_workspace_role_presets` for PostgreSQL enum values.
- Reworked `permissions_for_role()` around explicit read, developer, reviewer, legacy member, and owner permission sets.
- Added `require_workspace_permission(permission)` in `app.dependencies.workspace`.
- Applied permission gates to core dataset, knowledge, folder, agent, human review, and evaluation routes.
- Updated member management API/UI defaults, role presets, role labels, and clearer role-model explanation.
- Split frontend folder-management controls from destructive resource cleanup permissions.
- Updated database schema and audit docs.

## Validation
Passed:
- `cd backend && uv run ruff check app/models/workspace.py app/services/workspace_service.py app/dependencies/workspace.py app/api/v1/datasets.py app/api/v1/knowledge.py app/api/v1/evaluations.py app/api/v1/human_reviews.py app/api/v1/folders.py app/api/v1/agents.py tests/test_auth_workspace.py tests/test_resource_folders.py tests/test_agents.py tests/test_evaluations.py`
- `cd backend && uv run pytest -s -q tests/test_auth_workspace.py tests/test_resource_folders.py tests/test_agents.py::test_agent_archive_requires_owner_and_is_workspace_scoped tests/test_evaluations.py tests/test_human_reviews.py` -> 39 passed
- `cd backend && uv run pytest -s -q` -> 138 passed
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`

Browser QA note:
- Playwright still cannot launch in this WSL environment because `sudo` requires a password and Chromium is missing `libnspr4.so`.

## Human Review Checklist
- Confirm the role semantics match the intended product: developer can build/run, reviewer can resolve reviews, viewer is read-only, owner manages destructive/admin controls.
- Confirm preserving operational legacy `member` permissions is acceptable for existing demo data.
- Check the Members page labels and disabled controls visually once WSL browser dependencies are installed.

## Interview Notes
This ticket is a good backend/product-integrity story: instead of only hiding buttons, the platform now exposes role presets and enforces key actions server-side with explicit permission errors. It shows how professional AI platforms separate builders, reviewers, viewers, and owners while keeping workspace isolation and auditability intact.
