# Tool And Guardrail Catalog Bounds

## Goal
Keep the Tools and Guardrails operations boards usable as runtime catalogs grow.

## Context
Both pages already had search and filter controls. Backend services also limit recent tool calls and guardrail failures to 8 records per item. The remaining issue was top-level card rendering: every matching tool or guardrail policy was still rendered at once.

## Requirements
- Bound the visible tool cards after search/filter.
- Bound the visible guardrail policy cards after search/filter.
- Show operator guidance when matched items exceed the render limit.
- Do not add folders to these catalogs yet because they are runtime definitions, not uploaded/user-created file libraries.

## Implementation
- Reused `MAX_VISIBLE_ADMIN_ASSETS` for tool and guardrail catalog card limits.
- Added `displayedTools`, `hiddenToolCount`, `displayedGuardrails`, and `hiddenGuardrailCount`.
- Added overflow notes that tell users what fields to search before changing workspace defaults or governance settings.
- Recorded the decision in the resource/file management audit.

## Verification
- `cd frontend && npm run build` passed.
- `git diff --check` passed.

## Follow-up
If tools become installable plugins or guardrails become user-authored policy packs, add folders or package grouping before exposing upload/install flows.
