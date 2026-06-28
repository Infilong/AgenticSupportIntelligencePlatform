# Evaluation Target Agent UI

## Goal
Make evaluation runs explicitly show which agent they are testing, so evaluation quality is not hidden inside a generic run history.

## Context
The backend already persists `evaluation_runs.agent_config_id` and agent summaries include evaluation posture. The frontend still posted the active agent implicitly and did not clearly show target-agent attribution in the evaluation form, operations board, or results dashboard.

## Requirements
- Add an explicit evaluation target agent selector.
- Send the selected agent ID in evaluation run requests, or `null` when the user chooses the default evaluation agent.
- Show target-agent labels in evaluation run search, selected run summary, operations board rows, and dashboard metrics.
- Keep evaluation folders, archive controls, and bounded run list behavior unchanged.

## Non-goals
- Do not change backend schema or evaluation scoring.
- Do not add agent folders in this ticket.
- Do not remove the existing active agent workflow.

## Implementation Notes
- Added `evaluationAgentId` frontend state.
- Initialized the evaluation target to the first loaded agent when available.
- Added agent-aware search terms for evaluation runs.
- Passed agent metadata into `EvaluationDashboard` so selected run results show the target agent name.

## Resource Lifecycle Audit Note
Current file-backed or import-backed user resources are:
- Knowledge documents: upload, detail, edit/reindex, move folder, delete.
- Datasets: import, inspect examples, edit labels, move folder, delete.
- Evaluation runs: create from JSONL, inspect results, move folder, archive.

The current UI organizes these growing resources with folder rails, search fields, bounded list rendering, and detail inspectors. Future upload/import surfaces must follow the same lifecycle rule before they are accepted.

## Validation Plan
- Run frontend production build.
- Run `git diff --check`.
- No backend tests are required because this ticket only uses existing API fields.

## Human Review Checklist
- Confirm the evaluation form makes the selected target agent obvious.
- Confirm search can find evaluation runs by agent name or ID.
- Confirm Data, Knowledge, and Evaluations still show folder-scoped lists instead of unbounded filename lists.
- Confirm delete/archive controls remain permission-aware.

## Interview Notes
This improves traceability: an evaluation result should be attributable to a specific agent configuration, not just a timestamped experiment. That matters when explaining model routing, RAG quality, guardrail behavior, and release readiness.
