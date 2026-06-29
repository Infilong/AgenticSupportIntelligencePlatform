# Resource-Backed Picker Bounds

## Goal
Keep frontend fields that can grow with user-created resource names from becoming long native dropdowns or expanding panels.

## Context
The app already manages file-backed and import-backed libraries with resource folders: knowledge documents, datasets, evaluation runs, and agent configs. The remaining frontend risk was workflow fields that select a resource by name. Even when backend-bounded, a native select can still feel like a hidden long list and does not communicate how the user should narrow choices.

## Requirements
- File-backed or import-backed resource libraries must remain folder-scoped, searchable, and bounded.
- Resource-backed workflow selectors must use search plus a visible bounded option list.
- Native selects are acceptable only for small fixed enums such as status, language, role, provider, or mode.
- Do not load all agents, documents, datasets, or runs into the browser for a selector.

## Implementation
- Replaced the Evaluation target-agent native select with a bounded searchable option list.
- Added `MAX_VISIBLE_AGENT_PICKER_OPTIONS` so the API limit matches the number of rendered agent options.
- Preserved the default evaluation-agent option and the selected-agent shortcut.
- Preserved selected agent visibility when the selected agent is outside the current search result page.

## Validation
- `cd frontend && npm run typecheck` passed.
- `cd frontend && npm run build` passed.
- `cd frontend && npm test -- --run` passed.
- `git diff --check` passed.

## Human Review Checklist
- Confirm Evaluation setup no longer presents a long dropdown of agent names.
- Confirm search remains the primary way to find an agent in a large workspace.
- Confirm file-backed libraries still use folders for organization rather than flat fields.

## Interview Notes
This is a product-scale detail: backend pagination alone is not enough. Resource-heavy workflows need bounded, searchable pickers and folder-scoped libraries so the UI remains usable as the workspace moves from demo data to real team data.
