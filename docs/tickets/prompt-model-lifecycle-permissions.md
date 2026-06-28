# Prompt And Model Settings Lifecycle Permissions

## Goal
Make prompt templates and model configs behave like professional admin-owned platform settings, not unbounded member-editable records. Owners should be able to create, activate, archive, inspect archived history, and keep active routing clean. Members can inspect active settings but cannot mutate them.

## Context
The app already supports prompt version creation/activation and model config creation/activation. Audit found two gaps:
- mutation routes used workspace-member access instead of owner/admin access.
- prompt/model collections had no archive lifecycle, so old versions/configs accumulated indefinitely.

This is not a file-upload surface, so folders are not required in v1. It is a growing admin collection, so it needs bounded UI, archive controls, and backend-enforced permissions.

## Requirements
- Add `archived_at` to `PromptTemplate` and `ModelConfig`.
- Default list endpoints hide archived records.
- `include_archived=true` returns archived history for admins/operators.
- Create, activate, and archive routes require workspace owner access.
- Activating archived records is impossible.
- Archived prompt templates are ignored by active prompt lookup and default prompt creation.
- Archived model configs are ignored by active model routing, agent assignment validation, and system health readiness.
- Archiving an active prompt/model deactivates it.
- Archiving a model config clears agent-level assignments that pointed at it.
- Frontend exposes show-archived toggles and owner-gated archive actions on Prompts and Models.
- Tests cover owner lifecycle, member denial, workspace isolation, archived filtering, and runtime exclusion.

## Non-goals
- Do not hard-delete prompt templates or model configs; historical AI run and cost explanations must remain inspectable.
- Do not add folders to prompts/models in this ticket.
- Do not add custom enterprise RBAC roles.
- Do not change real provider behavior beyond excluding archived configs from selection/routing.

## Test Plan
- Backend prompt template tests for archive, include_archived, activation denial after archive, member mutation denial.
- Backend model config tests for archive, include_archived, activation denial after archive, member mutation denial, agent assignment clearing.
- Existing agent/model/prompt tests should still pass.
- Frontend typecheck/build.

## Acceptance Criteria
- Members cannot create, activate, or archive prompt/model settings.
- Owners can archive stale prompt/model records.
- Archived records do not appear in normal dropdowns or active routing.
- Archived history remains available when explicitly requested.
- UI makes archive state and permissions clear.


## Implementation Record
Implemented owner-gated lifecycle management for prompt templates and model configs.

Backend changes:
- Added `archived_at` to `PromptTemplate` and `ModelConfig`.
- Added soft-archive endpoints for prompt templates and model configs.
- Switched create, activate, and archive routes to workspace-owner permission.
- Default list routes hide archived records; `include_archived=true` returns full history.
- Archived prompts/models are excluded from active runtime lookup, provider readiness, and model assignment validation.
- Archiving a model config clears agent-level model assignments that referenced it.

Frontend changes:
- Added show-archived toggles and archive buttons to Prompts and Models.
- Disabled prompt/model mutation controls for non-owner users.
- Kept archived configs out of active routing summaries and agent model selection.

Verification:
- `cd backend && uv run ruff check .`: passed.
- Focused backend tests for prompt/model lifecycle, agent model assignment, auth workspace permissions, and system health: 36 passed.
- Full backend suite passed with `cd backend && uv run pytest -s -q`: 136 passed.
- `cd frontend && npm test -- --run`: passed.
- `cd frontend && npm run build`: passed.
- `make backend-migrate`: applied `0016_prompt_model_archive`.
- `docker compose up -d --build api frontend`: rebuilt and restarted local app services.
- Live API smoke passed for prompt archive, model archive, archived filtering, and model archive clearing agent assignment.
- `make frontend-e2e-docker`: passed.
