# Milestone 10: Frontend Trace And Evaluation UI

## Goal
Build a professional, local-first React UI that lets a user run the core demo workflow from the browser: auth, workspace selection, dataset import, document upload, support-agent run, graph trace inspection, human review, evaluation dashboard, and cost summary.

## Context
Backend milestones 2-9 expose the required workspace-scoped APIs. The current frontend is still the Milestone 1 placeholder shell.

Relevant docs:
- `docs/PROJECT_CONTEXT.md`
- `docs/api-design.md`
- `docs/observability-design.md`
- `docs/evaluation-design.md`
- `docs/architecture-tree.md`

## Requirements
- Replace the placeholder React app with an internal-product UI.
- Add login/register controls using JWT auth.
- Add workspace list/create/select flow.
- Add workspace tabs for overview, datasets, documents, agent, trace, human reviews, evaluations, and costs.
- Use the real backend API contracts; no fake frontend-only data for completed workflows.
- Show graph trace steps, tool calls, token/cost fields, latency, final answer, route decision, and errors.
- Show evaluation metrics by language and mode.
- Show cost totals and purpose breakdown.
- Keep UI compact, professional, and usable on desktop/mobile.

## Non-goals
- No new frontend router dependency.
- No complex component library.
- No screenshots/GIFs yet; those belong to portfolio packaging.
- No arbitrary language plugin UI.

## Design Plan
- Implement a typed API client inside `frontend/src/App.tsx` for this milestone.
- Keep state local to the single-page app to avoid introducing routing/store complexity.
- Use a tabbed workspace layout with focused panels.
- Use textareas for JSONL/document/content workflows because v1 is an internal tool.
- Parse JSON string fields only for display; preserve raw values on API calls.
- Update CSS to a dense internal SaaS style with stable layout dimensions.

## Files Likely To Change
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `docs/tickets/milestone-10-frontend-ui.md`
- `docs/learning/milestone-10-frontend-ui.md`
- `docs/architecture-tree.md`
- `README.md`

## Test Plan
- `make frontend-test`
- `make frontend-build`
- `make backend-test` to ensure schema/API behavior remains stable.
- Optional Docker smoke if frontend build exposes backend integration problems.

## Acceptance Criteria
- User can register/login, create/select workspace, import dataset, upload docs, run agent, inspect trace, resolve review, run evaluation, and view costs from browser.
- UI renders real API results and errors clearly.
- Evaluation dashboard separates metrics by mode and language.
- Graph trace viewer is clear enough to support interview explanation.
- Validation passes and commit is pushed.

## Risks
- Frontend may become too large in one file; acceptable for this milestone, but extraction can happen later.
- API errors must be visible, not swallowed.
- UI must not claim async worker behavior that v1 does not implement.
- Costs are estimates and must be labeled as such.

## Human Review Checklist
- Can you run the core demo from the browser without hidden steps?
- Are trace/evaluation/cost panels understandable in an interview?
- Are token economy and human-review routing visible enough?
- Does the UI feel like an internal AI platform rather than a tutorial landing page?

## Interview Notes
Be able to explain why the frontend prioritizes traceability, evaluation evidence, and cost visibility over decorative design.

## Implementation Record
Implemented as a compact single-page React internal tool.

Changed areas:
- Replaced the placeholder frontend shell with an authenticated workspace-aware app.
- Added real API calls for auth, workspaces, datasets, labels, documents, agents, traces, human reviews, evaluations, and costs.
- Added graph trace viewer with step output, tool calls, latency, token, cost, and error fields.
- Added evaluation dashboard with metrics by mode and language plus per-case results.
- Added cost dashboard with ledger totals and purpose breakdown.
- Updated styling to a dense internal SaaS layout.

Validation performed:
- `make frontend-test` passed.
- `make frontend-build` passed.

Known limitations:
- The UI intentionally keeps state in one file for this milestone; component extraction can happen after browser demo review.
- No browser E2E tests yet.
- The UI depends on the backend being available at `VITE_API_BASE_URL` or `http://localhost:8000`.
