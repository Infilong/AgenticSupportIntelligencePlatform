# Prompt and Model History Total Count Envelope

## Goal
Make prompt-template and model-config histories truthful under backend pagination by returning page metadata instead of bare arrays. Admins should see how many matching versions/configs exist and Next should be controlled by backend `has_next`.

## Context
Prompt and model admin histories already supported `status`, `include_archived`, `search`, `limit`, and `offset`, and the frontend loaded bounded history pages. Like the review queue, audit logs, tools, and guardrails, these admin histories still guessed continuation from page size. Prompt/model histories are important because they prove production-style AI governance: versioning, activation, archive lifecycle, and model routing.

## Requirements
- Change `GET /api/v1/workspaces/{workspace_id}/prompt-templates` to return `items`, `total`, `limit`, `offset`, and `has_next`.
- Change `GET /api/v1/workspaces/{workspace_id}/model-configs` to return the same envelope.
- Preserve status, archived visibility, search, limit, offset, and workspace isolation.
- Keep summary loads working for active prompt/model cards.
- Update history pages to display `shown of total` and use backend `has_next`.
- Update focused tests for totals, filters, offsets, archive lifecycle, and workspace isolation.

## Non-goals
- Do not change prompt activation or model routing behavior.
- Do not add folders to prompt/model histories; they are versioned admin configs, not uploaded resources.
- Do not introduce cursor pagination in v1.

## Implementation Summary
- Added `PromptTemplateListResponse` and `ModelConfigListResponse`.
- Extracted shared prompt/model filter helpers and added `count_templates()` / `count_configs()`.
- Updated list routes to return envelopes.
- Updated React summary/history loaders to read `items`, and history pages to track totals and `has_next`.
- Added prompt/model clear-state helpers for permission or workspace changes.
- Updated tests to assert filtered totals and page metadata.

## Validation
- Backend: `uv run pytest -s -q tests/test_prompt_templates.py tests/test_model_configs.py`
- Backend lint: `uv run ruff check app tests/test_prompt_templates.py tests/test_model_configs.py`
- Frontend: `npm run typecheck`
- Frontend: `npm run build`

## Risks
- This changes list API contracts for prompt/model endpoints; in-repo callers are updated, but external clients must read `items`.
- Summary loads still request up to 500 non-archived rows for admin summary cards. That remains acceptable for local-first v1 but should eventually move to dedicated summary endpoints.

## Human Review Checklist
- Confirm prompt and model history pages show useful `shown of total` counts.
- Confirm archive, activation, and search flows still refresh history correctly.
- Confirm summary cards remain understandable and are not confused with global totals.

## Interview Notes
This ticket demonstrates AI governance maturity: prompts and model routes are versioned operational assets, and the backend owns filtered history counts. It also shows the tradeoff between a simple local-first summary fetch and production-grade dedicated summary endpoints.
