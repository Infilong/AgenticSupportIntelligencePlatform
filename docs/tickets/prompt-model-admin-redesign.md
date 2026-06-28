# Prompt and Model Admin Redesign

## Goal
Make Prompt settings and Model settings feel like professional AI platform admin screens. The user should understand active prompt versions, model-purpose routing, token-price configuration, and how changes affect the next LangGraph run without needing a manual.

## Implemented Changes
- Reframed Prompts as "Prompt operations" with readiness status, active versions, language coverage, and workflow prompt cards.
- Added prompt summary metrics for active prompts, total versions, classifier version, and drafter version.
- Rebuilt the prompt creation workflow as a controlled versioning panel with clear next actions: create version, run agent, inspect trace.
- Added prompt version history cards with active status and activation controls.
- Reframed Models as "Model routing" with configured-purpose coverage, live-provider count, max context, and routing readiness.
- Rebuilt model configuration creation into grouped controls for purpose/provider/model and cost/context profile.
- Added active purpose routing cards to show which model is used for classification, drafting, evaluation, and compression purposes.
- Added responsive settings CSS shared by prompt and model admin surfaces.

## Verification
- `npm run test` -> passed (`tsc --noEmit`).
- `npm run build` -> passed (`tsc -b && vite build`).

## Human Review Notes
Visually review:
- Prompt settings: active prompt cards, create-version form, template textarea focus, and activate buttons.
- Model settings: purpose routing cards, provider preset behavior, cost/context inputs, and activate buttons.
- Narrow viewport: settings summary, workbench, and history cards should collapse cleanly.
- After creating or activating a prompt/model config, run the agent and confirm Trace/Cost pages expose the selected prompt/model metadata.

## Remaining Risks
- This is a frontend/admin workflow redesign only; backend prompt/model APIs were not changed.
- A future backend/frontend ticket could add diffing between prompt versions and warnings when live providers are active without required environment keys.
