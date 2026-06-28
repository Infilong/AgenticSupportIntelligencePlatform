# Cost Drilldown Total Count Envelope

## Goal
Make the Usage & Costs page pagination accurate as AI ledger rows and graph-run spend records grow. The dashboard already uses backend filtering and limits, but the frontend still guessed whether another page existed from the number of rows returned.

## Context
Token economy is a first-class project requirement. Cost accounting totals must remain full-workspace values, while drilldown lists need their own filtered totals for search/status investigations. This follows the same bounded-list pattern now used for datasets, knowledge documents, agents, prompts, models, reviews, audit logs, tools, guardrails, and trace run history.

## Requirements
- Keep full accounting totals unfiltered: total AI calls, tokens, estimated cost, latency, failure counters, and budget usage.
- Add filtered drilldown totals for graph-run spend rows and AI run ledger rows.
- Preserve existing `recent_runs` and `recent_ai_runs` arrays.
- Use backend totals to drive frontend "Next" buttons and shown-of-total labels.
- Prove counts are filtered and workspace-scoped.

## Non-goals
- Do not change token/cost calculation formulas.
- Do not change budget policy enforcement.
- Do not add deletion for cost or AI run ledger rows; they are immutable observability evidence in v1.
- Do not redesign the whole cost dashboard.

## Design Summary
- Added `graph_run_total` and `ai_run_total` to the backend `CostSummary` object and API response.
- `graph_run_total` counts distinct graph runs matching the current graph-run spend filters.
- `ai_run_total` counts AI ledger rows matching the current AI ledger filters.
- Frontend pagination now uses these totals instead of guessing from page size.
- Dashboard copy now states that drilldown totals are backend-owned while accounting totals remain full-workspace.

## Test Plan
- Extended the existing cost drilldown test to assert filtered graph-run and AI-ledger totals.
- Extended workspace-isolation assertions so another workspace sees zero filtered totals and no rows.
- Run backend AI observability tests, ruff, frontend typecheck, frontend build, and `git diff --check`.

## Acceptance Criteria
- Cost drilldown pagination remains correct when a filtered result has exactly one full page or a partial page.
- Search/status filters return accurate totals for graph-run spend and AI ledger rows.
- Full accounting totals are not narrowed by drilldown filters.
- Other workspaces cannot infer cost drilldown counts.

## Human Review Checklist
- Confirm the Cost page labels make it clear that accounting totals and drilldown totals are different.
- Confirm Next buttons disable based on backend totals.
- Confirm cost/ledger records remain non-destructive observability evidence.

## Interview Notes
- Explain why a cost dashboard needs both full accounting totals and filtered drilldown totals.
- Explain why frontend page-size guessing fails at scale.
- Explain why AI ledger rows are immutable evidence for audits, debugging, and token-economy tuning.
