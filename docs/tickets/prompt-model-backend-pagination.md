# Prompt And Model Backend Pagination

## Goal
Add backend-owned search, status filtering, and pagination for prompt-template and model-config histories.

## Context
Prompt templates and model configs are versioned control-plane records. They are not uploaded files and do not need resource folders, but their histories can grow as teams test prompts, change providers, tune pricing, and archive old routes. The frontend already bounds rendered cards, but the APIs still returned whole histories.

## Requirements
- Add `search`, `status`, `limit`, and `offset` to prompt-template listing.
- Add `search`, `status`, `limit`, and `offset` to model-config listing.
- Preserve existing `include_archived` behavior for current callers.
- Support status values: `all`, `active`, `draft`, `archived`.
- Keep workspace scoping and permission dependencies unchanged.
- Add tests for paging, search, active/draft/archived filters, and archive behavior.

## Non-goals
- Do not change prompt or model create/activate/archive lifecycle semantics.
- Do not change frontend settings pages in this ticket. A separate UI ticket should split active summaries from backend-paged history lists so the summaries stay accurate while histories page.
- Do not add folders to prompts or models.
- Do not add total-count endpoints.

## Design Plan
- Extend `PromptTemplateService.list_templates()` with `status_filter`, `search`, `limit`, and `offset`.
- Extend `ModelConfigService.list_configs()` with the same controls.
- Add typed query aliases to `prompt_templates.py` and `model_configs.py`.
- Search prompt history by name, language, version, id, and template source.
- Search model config history by provider, model, purpose, id, and context size.

## Test Plan
- `cd backend && uv run pytest -s -q tests/test_prompt_templates.py tests/test_model_configs.py`
- `cd backend && uv run ruff check .`

## Acceptance Criteria
- Existing prompt/model list callers still work without query params.
- Prompt/model APIs can return backend-filtered pages.
- Archived records can be requested directly with `status=archived`.
- Search is applied before pagination.

## Risks
- Frontend still needs a follow-up ticket to consume these query params without weakening active summary panels.
- Search-specific total counts are not available yet.
- Prompt/model status strings are now duplicated between backend and frontend conventions.

## Human Review Checklist
- Confirm prompt/model API query names match the frontend history filters.
- Confirm archived records are excluded by default.
- Confirm active route behavior is unchanged.

## Interview Notes
This is the backend half of making prompt/model registries production-like. It preserves the active routing semantics while adding the API surface needed for scalable version history and provider-route auditing.
