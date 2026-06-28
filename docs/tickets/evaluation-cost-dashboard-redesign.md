# Evaluation and Cost Dashboard Redesign

## Goal
Make the Evaluation and Cost pages feel like professional AI operations dashboards instead of raw forms and tables. These screens should prove quality, multilingual behavior, baseline comparison, and token economy to both engineering reviewers and interviewers.

## Implemented Changes
- Reframed Evaluation as an "Evaluation lab" for comparing direct LLM, vector RAG, and system v1.
- Added mode cards with plain-language explanations for what each baseline proves.
- Added run summary metrics and a clearer run selector.
- Rebuilt the EvaluationDashboard to show pass rate, failed cases, languages covered, latency, prompt tokens, and estimated cost.
- Added mode/language metric cards so English, Japanese, and Chinese quality can be compared quickly.
- Highlighted failed evaluation cases with route, latency, prompt tokens, cost, answer, scores, and citations.
- Reframed Cost as a token-economy dashboard backed by the AI run ledger.
- Added cost posture, top cost driver, summary metrics, cost by purpose, cost controls, and cost by model cards.
- Added responsive CSS for evaluation and cost operations layouts.

## Verification
- `npm run test` -> passed (`tsc --noEmit`).
- `npm run build` -> passed (`tsc -b && vite build`).

## Human Review Notes
Visually review:
- Evaluation page: mode cards, JSONL editor focus, run button, run selector, and selected results dashboard.
- Evaluation dashboard: language/mode cards are readable and failed cases are obvious.
- Cost page: token posture, purpose cards, model cards, and cost-control policy list are understandable without extra docs.
- Mobile or narrow viewport: evaluation/cost grids collapse into one column cleanly.

## Remaining Risks
- The frontend now presents evaluation and cost data better, but the backend metric set is still basic. A later ticket should add richer metrics such as citation accuracy, groundedness pass rate, language preservation pass rate, and baseline deltas if not already emitted for every run.
- Browser-level visual QA is still needed to confirm the final spacing in a real viewport.
