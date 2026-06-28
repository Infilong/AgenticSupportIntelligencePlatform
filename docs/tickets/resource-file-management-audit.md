# Resource And File Management Audit

## Goal
Audit whether uploaded/imported user-owned resources can be managed after creation, and record the frontend rule that growing file/resource-name areas must be organized rather than allowed to expand indefinitely.

## User Concern
The app should not only provide upload/import controls. If a user owns a file-backed resource and has enough permission, they should be able to inspect, edit or reindex where relevant, move, and delete it. Frontend areas that can grow with many file names must be managed through folders, search, bounded lists, pagination, or detail inspectors.

## Current Findings
- Knowledge documents: backend supports upload, list, detail, reindex/edit, move to folder, and delete. Frontend shows folders, search, bounded document list, edit/reindex form, move control, delete control, and bounded chunk inspector.
- Datasets: backend supports import, list, folder move, example inspection/labeling, and delete. Frontend shows dataset folders, search, bounded dataset list, move control, delete control, and bounded example inspector.
- Resource folders: backend supports create, list, rename, and delete-empty-folder with workspace checks. Frontend supports folder creation, selection, rename, delete, and folder-scoped views.
- Permissions: backend gates destructive resource operations with `resources:delete` and folder movement/management with `resource_folders:manage`. Tests cover owner success, viewer denial, non-empty folder denial, and cross-workspace folder rejection.

## Risk Areas To Keep Watching
- Future file-backed resources must not add upload-only flows.
- Future lists of prompts, model configs, tools, evaluation cases, or artifacts may need the same bounded-list/search/detail pattern if they become large, even if they are not file uploads.
- Frontend currently uses client-side filtering for local-first Data/Knowledge views. This is acceptable for the small-team v1 but should move toward backend pagination/filtering before larger deployments.

## Durable Rule Added
- `docs/PROJECT_CONTEXT.md` now defines resource and file management as a standing rule.
- `AGENTS.md` now includes a concise always-read reminder that uploaded/imported resources need permission-gated management paths and folder/search/bounded UI.

## Validation
Documentation-only ticket. Existing backend behavior is covered by `backend/tests/test_resource_folders.py`. Run that test when changing resource-folder, dataset, or knowledge-document management code.

## Human Review Checklist
- Confirm the Data and Knowledge pages are understandable visually: users should see folders, current folder, upload/import target, search, move, delete, and bounded inspectors.
- Confirm destructive controls are disabled or hidden clearly when the user lacks permission.
- Confirm future upload/file-list tickets follow the same pattern before implementation is accepted.

## 2026-06-29 Follow-up Audit
- File/import-backed resources remain folder-bounded in the UI: datasets, knowledge documents, and evaluation runs.
- Knowledge documents and datasets have permission-gated delete controls in both backend and frontend.
- Evaluation runs are archived instead of hard-deleted so result evidence, cost metrics, and audit history remain inspectable.
- Prompt templates, model configs, tool configs, and guardrail policies are not file uploads, but they still need searchable/archivable operations boards if their lists continue to grow. Add folders only when these become user-managed libraries rather than small admin catalogs.
- Future tickets must not add an upload/import field without a matching management path: inspect, edit or reindex where relevant, move/organize, and delete or archive with permission checks.

## 2026-06-29 Agent Resource Follow-up
- Agent configs are now managed as folder-bounded workspace resources through the `agent_config` folder type.
- Agents use archive rather than hard delete, preserving run, trace, evaluation, and cost evidence.
- The Agents page now follows the same folder rail, search, bounded list, and move-control pattern used for file/import-backed resources.

## 2026-06-29 Prompt And Model Catalog Follow-up
- Prompt templates and model configs remain admin catalogs rather than folder-backed file libraries.
- Their history panels are now searchable, status-filtered, bounded, and archive-aware.
- Long prompt source text is collapsed by default so version history remains scannable.

## 2026-06-29 Audit Trail Follow-up
- Audit logs are loaded through the existing workspace-scoped, server-limited API.
- The Audit page now adds frontend search, impact filtering, actor filtering, and bounded rendering so admin review remains usable as events grow.

## 2026-06-29 Cost Workbench Follow-up
- Cost and AI ledger views now provide shared search plus graph-run and AI-call status filters.
- Spend driver lists are bounded so token/cost investigation remains usable as agents, model routes, and runs grow.
