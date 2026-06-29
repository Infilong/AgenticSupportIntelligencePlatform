# Frontend Resource List Scale Audit

## Goal
Ensure frontend fields that can grow with uploaded file or resource names stay navigable as workspaces accumulate documents, datasets, agents, and evaluation runs.

## Context
The user flagged that frontend fields with many file names should be managed through folders instead of growing into long flat controls. The app already has folder-backed resource APIs and several prior UI tickets, so this ticket audits the current implementation and tightens the remaining bounded-summary behavior.

## Requirements
- Uploaded or file-like workspace resources must be folder-scoped where users create, move, edit, or delete them.
- Folder pickers must be searchable and bounded.
- Resource lists must be loaded by folder/search/page instead of rendering every matching name.
- Selected-resource inspectors must be searchable and bounded for large internals such as examples and chunks.
- Non-file operational histories should not get fake folders; they must use search, status filters, pagination, and bounded summary loaders.

## Audit Result
Folder-managed resource libraries:
- Knowledge documents: folder panel, searchable folder picker, backend folder/search/offset/limit listing, row-level move, edit/reindex, delete, bounded chunk inspector.
- Datasets: folder panel, searchable folder picker, backend folder/search/offset/limit listing, row-level move, delete, bounded example inspector.
- Agent configs: folder panel, backend folder/search/offset/limit listing, row-level move, archive controls, bounded active-agent selector from the current page.
- Evaluation runs: folder panel, backend folder/search/status/archive/offset/limit listing, row-level move, archive/delete controls, bounded baseline picker in current scope.

Bounded non-folder operational histories:
- Prompt templates use status/search/offset/limit history browsing. The always-loaded summary now requests active prompts only with the normal admin asset limit.
- Model configs use status/search/offset/limit history browsing. The always-loaded summary now requests active model routes only with the normal admin asset limit.
- Tools, guardrails, traces, reviews, audit logs, and cost ledger views already use search/filter/pagination controls.

## Changes
- Changed the prompt summary loader from an all-history 500-record fetch to an active-only bounded fetch.
- Changed the model summary loader from an all-history 500-record fetch to an active-only bounded fetch.
- Updated prompt summary copy so it no longer implies the summary list contains all prompt versions.

## Non-goals
- Do not add fake folders for prompts, model configs, tools, guardrails, or audit events.
- Do not change backend schemas.
- Do not refactor the large frontend shell.
- Do not replace the workspace selector; workspaces are not uploaded file resources.

## Validation Plan
- Run frontend typecheck.
- Run frontend production build.
- Run frontend unit test wrapper.
- Run focused backend tests for folder-managed resources and prompt/model list contracts.

## Human Review Checklist
- Confirm Knowledge, Datasets, Agents, and Evaluations are the only folder-managed product resource libraries for now.
- Confirm prompt/model histories still show full searchable paginated history when opened directly.
- Confirm active summaries remain accurate after creating or activating prompt/model configs.
- Confirm no page quietly loads hundreds of uploaded file names into a single field.

## Interview Notes
This is a useful product-engineering tradeoff: folders belong to user-managed libraries where people upload, organize, move, and delete resources. Prompt/model/tool histories are operational configuration streams, so the better scale control is bounded search, filters, pagination, and active summaries rather than inventing folders for everything.
