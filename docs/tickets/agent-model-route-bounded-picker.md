# Agent Model Route Bounded Picker

## Goal
Replace the Agent page's growing model-config dropdown with a searchable, backend-bounded picker so agent model routing stays usable as a workspace accumulates provider/model configurations.

## Context
The app already stores `agent_configs.model_config_id` and the backend model config list API supports `search`, `status`, `limit`, `offset`, totals, and `has_next`. The Agent configuration control center still rendered all loaded model configs in a native select. That violates the frontend large-field rule: resource-name fields that can grow should not become long flat dropdowns.

## Requirements
- Keep the existing agent update payload and backend behavior unchanged.
- Load model route options from `GET /model-configs` with a small limit and optional search.
- Preserve the selected model route even when it is not in the current search result page.
- Keep a clear fallback option for workspace purpose routing.
- Show how many matching routes are loaded and ask the user to search when there are more.
- Do not add folders for model configs; they remain an admin catalog, not a file-backed resource library.

## Non-goals
- Do not change model routing execution semantics.
- Do not change model config archive/activation behavior.
- Do not add a new backend endpoint.
- Do not redesign the entire Agent page in this ticket.

## Implementation Summary
- Added `MAX_VISIBLE_MODEL_ROUTE_OPTIONS` and dedicated `agentModelSearch` / `agentModelOptions` state.
- Added `loadAgentModelOptions()` using the existing paginated model config API with `limit`, `offset`, and `search`.
- Added an Agent-tab effect that loads bounded model route options only when the user can read models.
- Replaced the native model-route select with a searchable listbox-style picker.
- Kept the workspace purpose routing fallback as an explicit first option.
- Preserved selected assigned model configs outside the current option page.
- Added compact CSS for model route option cards.

## Validation
- Frontend: `npm run typecheck`
- Frontend: `npm run build`

## Risks
- The Agent page still uses a native select for the active agent field, but that select is bounded by the current folder/page and paired with the foldered Agent library. A future ticket can replace it with direct selection from the library only.
- Search calls run on every input change through the existing effect. This is acceptable for local-first v1; larger deployments may need debounce or a reusable async entity picker.

## Human Review Checklist
- Confirm Agent > Model route is understandable without opening the Models admin page.
- Confirm searching by provider, model, purpose, or id narrows the route options.
- Confirm clearing to workspace purpose routing is obvious.
- Confirm saving runtime controls still persists the selected model route.

## Interview Notes
This ticket shows product-scale thinking: once backend list APIs are paginated, dependent configuration fields must stop borrowing unbounded arrays. The UI now treats model routes as searchable operational assets while the backend remains the source of truth for workspace-scoped model configs.
