# Milestone 10: Frontend Trace And Evaluation UI

## What Was Built
Milestone 10 replaced the placeholder Vite page with a real internal AI platform UI. The app supports authentication, workspace selection, dataset import, label editing, document upload, agent runs, graph trace inspection, human review resolution, evaluation runs, and cost summaries.

## Why Companies Care
AI/backend engineers are more valuable when they can expose backend AI behavior clearly to product managers, reviewers, and operators. A traceable UI helps teams debug model behavior, verify citations, inspect routing decisions, and understand token cost without reading database rows.

## How This Project Uses It
The frontend calls real workspace-scoped APIs. The graph trace viewer shows every LangGraph step, tool call, latency, token, cost, retry, and error field available from the backend. The evaluation page shows metrics by language and baseline mode, while the cost page shows AI run ledger aggregates.

## Design Tradeoffs
- A single-file React app keeps the milestone reviewable and avoids premature frontend architecture.
- Local component extraction is postponed until the browser demo flow is validated.
- The UI favors dense operational clarity over marketing-style design.
- JSONL and textareas are acceptable for v1 because this is an internal local-first tool.

## Failure Modes
- If API errors are hidden, users cannot debug backend or permission issues.
- If trace data is too compressed, the UI loses its main interview value.
- If evaluation metrics are not separated by language and mode, important multilingual regressions become invisible.
- If estimated costs are presented as exact billing data, the product story becomes misleading.

## Interview Explanation
A strong explanation is:

"I built the frontend as an internal AI operations surface, not a chatbot skin. The important UI is the graph trace, evaluation dashboard, human review queue, and token-cost summary. This makes the LangGraph workflow inspectable and gives product or engineering reviewers evidence for why a response was finalized, refused, or routed to review."
