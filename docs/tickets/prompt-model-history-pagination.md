# Prompt And Model History Pagination

## Goal
Keep prompt-template and model-configuration history usable as experiments grow. These resources are not uploaded files, but repeated prompt/model versions can still create long name-heavy admin histories if the frontend loads and filters everything locally.

## Context
The backend already supports workspace-scoped `limit`, `offset`, `status`, `search`, and archived visibility for prompt templates and model configs. Earlier folder tickets covered uploaded/file-backed resources such as datasets, knowledge documents, and evaluation runs. This ticket applies the same bounded-resource rule to admin histories that grow through configuration versions.

## Requirements
- Preserve active prompt/model summaries used by readiness cards and routing summaries.
- Load history cards through backend filters instead of local full-list filtering.
- Reset history page when search, status, archive visibility, or mutation changes.
- Keep archived visibility explicit.
- Keep pagination simple and honest for the local-first app.

## Non-goals
- No backend schema changes.
- No folder semantics for prompt templates or model configs in this ticket.
- No virtualized table framework or infinite scroll.
- No changes to model provider behavior.

## Implementation Notes
- Added separate frontend state for summary lists and backend-loaded history lists.
- `loadPromptTemplates()` and `loadModelConfigs()` now fetch bounded summary data for active/readiness views.
- `loadPromptTemplateHistory()` and `loadModelConfigHistory()` fetch status/search/archive filtered pages from the backend.
- Prompt/model create, activate, and archive actions refresh both summaries and the current history page.
- The prompt/model admin panels now show page controls and backend-loading notes instead of hidden local overflow counts.

## Validation
- `cd frontend && npm run typecheck` -> passed.
- `cd frontend && npm run build` -> passed.

## Human Review Checklist
- Confirm prompt and model history controls keep focus while typing.
- Confirm active summary cards still reflect active versions/configs.
- Confirm archived records appear only when requested or when the archived status filter is selected.
- Confirm Next/Previous behavior is clear enough for a local-first admin console.

## Interview Notes
This demonstrates a scale-aware UI/backend boundary: the frontend keeps rich admin controls, but history growth is handled by backend filters and offsets instead of unbounded client-side lists. It also preserves the distinction between folder-managed uploaded resources and versioned configuration resources.
