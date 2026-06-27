# Prompt Settings Admin Surface

## Goal
Give developers/admins a real prompt-operations surface instead of only showing prompt versions after a run.

## Audit Finding
Prompt templates were persisted and visible in trace, but users could not list, create, or activate prompt versions. That made prompt versioning more demonstrable than operational. A professional AI platform needs prompt settings for controlled iteration and debugging.

## Changes Made
- Added workspace-scoped prompt template API:
  - `GET /api/v1/workspaces/{workspace_id}/prompt-templates`
  - `POST /api/v1/workspaces/{workspace_id}/prompt-templates`
  - `POST /api/v1/workspaces/{workspace_id}/prompt-templates/{template_id}/activate`
- Expanded `PromptTemplateService` with list, create-version, active selection, activation, and workspace-scoped lookup.
- Updated graph execution to use the active prompt template when one exists; otherwise it lazily creates the default.
- Added backend tests for create/list/activate, workspace isolation, and active prompt usage in the next agent run.
- Added a frontend `Prompt settings` page for developers/admins to create prompt versions, mark a version active, inspect active prompts, and view all prompt source text.

## Verification
- `make backend-lint`
- `make backend-test`
- `npm run test`
- `npm run build`
- `docker compose up -d --build api frontend`
- Live API smoke confirmed an admin-created active prompt is used by the next agent run and appears in trace.

## Remaining Risks
- Prompt names are currently constrained to known prompt families in the frontend; backend accepts any valid name.
- There is no diff viewer between prompt versions yet.
- There is no evaluation comparison by prompt version yet.
- Role-based admin permissions are not implemented; current workspace membership is the authorization boundary.

## Next Recommended Ticket
Add a prompt-version comparison and evaluation link: run evaluation grouped by prompt template version so developers can see whether a prompt change improves quality/cost before keeping it active.
