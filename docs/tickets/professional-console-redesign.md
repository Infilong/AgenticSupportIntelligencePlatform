# Professional Console Redesign Pass

## Goal
Move the browser UI away from a toy/demo wizard and toward a professional internal console for AI engineers, support admins, and product reviewers.

## Audit Findings
- Navigation was a flat numbered list, so setup, operation, and observability felt equally important and confusing.
- The overview explained the app more than it operated the app. Users needed to read copy instead of seeing state, next actions, and risk.
- Admin and developer concerns were hidden across pages instead of visible as queues, traces, evaluation, and cost controls.
- The agent page did not offer fast realistic test prompts for normal, risky, and multilingual cases.
- Styling looked like a demo shell: dark sidebar, low hierarchy, weak focus states, and inconsistent operational density.

## Changes Made
- Grouped navigation into Setup, Operate, and Observe while preserving the 1-8 workflow order.
- Added workspace context, readiness progress, grouped nav, and logout to a lighter professional sidebar.
- Added a top workspace status strip for readiness, document count, pending reviews, AI runs, and token cost.
- Rebuilt the overview as an operations console with system readiness, admin queue, developer toolbox, and workflow map.
- Added sample agent prompt chips for English refund, Japanese security, Chinese privacy escalation, and prompt injection cases.
- Improved status tone handling so successful graph steps render as successful instead of bad.
- Replaced the old visual system with a cleaner admin-console style using compact cards, stronger focus states, lighter navigation, and responsive layouts.

## Verification
- `npm run build`
- `npm run test`
- `curl http://127.0.0.1:5173`
- `curl http://127.0.0.1:8000/health`
- `docker compose ps`

## Remaining Product Risks
- The UI is still a single large React file. It should be split into page/components before deeper UI work.
- There is no real admin settings API yet, so this pass exposes real controls and status rather than fake configurable settings.
- Browser screenshot verification was not captured from Codex because no usable headless browser path was available in this environment. Manual visual QA should be done at `http://localhost:5173`.
- The review page still uses one shared decision control. A later pass should make each review row independently editable and show richer run context inline.

## Next Recommended Ticket
Split the frontend into feature components and improve the human-review and trace pages with per-row decisions, side-by-side evidence, model call details, and guardrail result summaries.
