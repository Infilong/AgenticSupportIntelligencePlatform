# Agent Model Routing Control

Date: 2026-06-28

## Goal
Expose the existing `agent_configs.model_config_id` as a real agent-level default model/provider route. The Agent page should show which model config a selected agent uses, let permitted workspace members assign or clear that route, and backend model calls should use the selected config instead of only the workspace active purpose fallback.

## Context
The professional platform objective requires agent pages to show model/provider configuration. The database already has `AgentConfig.model_config_id`, but the API response, update payload, frontend Agent page, token-budget planner, and model provider do not use it. That creates a credibility gap: the UI can describe model routing, but agents cannot own model routing.

## Requirements
- Add `model_config_id` to agent create/update/read contracts.
- Validate that an assigned model config belongs to the same workspace.
- Allow clearing the agent model override.
- Include selected assigned model config details in the agent operational summary.
- Use the selected agent model config for classification and draft-response budget planning and AI run recording.
- Keep fallback behavior: if no agent model config is selected, use active workspace model config by purpose, then deterministic mock pricing.
- Record audit metadata when assignment changes.
- Add tests for assignment, cross-workspace rejection, clearing, and AI run provider/model selection.
- Update the Agent UI with a model routing section backed by real model config data.

## Non-goals
- Do not add API key storage.
- Do not add per-node or per-purpose agent routing matrices.
- Do not change model config activation semantics.
- Do not add a database migration because the foreign key already exists.

## Design Plan
Backend:
- Extend agent schemas with `model_config_id`.
- Add model config lookup/validation in `AgentService`.
- Add an optional `model_config_id` override to `ModelConfigService.resolve_pricing()`.
- Pass the selected agent model config through `SupportAgentState`, budget planning, and LangChain model provider calls.
- Include assigned model config details in `AgentOperationalSummaryResponse`.

Frontend:
- Extend `Agent` and `AgentOperationalSummary` types.
- Add a model routing card to `AgentPanel()`.
- Add a select control in runtime controls for default model route.
- Show provider, model, purpose, max context, active state, and fallback explanation.

## Test Plan
- Backend focused tests in `backend/tests/test_agents.py`.
- Existing model config tests should continue to pass.
- Frontend type/build checks should pass.

## Acceptance Criteria
- A workspace user can assign an owned model config to an agent.
- A workspace user cannot assign another workspace model config.
- Clearing the assignment restores fallback model routing.
- Agent summary returns selected model config metadata.
- Agent AI runs record the selected provider/model when an assigned mock model config exists.
- UI makes model routing visible and editable without placeholder data.

## Human Review Checklist
- Confirm the Agent page clearly distinguishes agent default routing from workspace active-purpose routing.
- Confirm the selected model config affects trace AI run provider/model fields.
- Confirm cross-workspace model configs cannot be assigned.
- Confirm no API keys or secrets are exposed.

## Interview Notes
This ticket demonstrates backend/product integrity: the platform does not merely show a model settings page; agent execution routes through a persisted, workspace-scoped model configuration and records the selected provider/model in the AI run ledger.
