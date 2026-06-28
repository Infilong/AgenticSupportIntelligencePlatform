# Uploaded Resource Lifecycle Audit

## Goal
Make sure frontend surfaces that create or upload reusable workspace assets do not become unbounded flat lists, and that users with enough permission can clean up what they create.

## Audit Result
The current app already uses resource folders for the file/name-heavy resource types:

- Knowledge documents: foldered, searchable, bounded list, move, edit/reindex, delete.
- Datasets: foldered, searchable, bounded list, move, delete, bounded example inspector.
- Agent configs: foldered, searchable, bounded list, move, archive.
- Evaluation runs: foldered, searchable, bounded list, move, archive.

Prompt templates, model configs, tools, guardrails, audit events, and cost rows are not upload files in the current product model. They are still searchable and bounded, but they do not use resource folders yet.

## Change Made
Evaluation runs were the lifecycle gap. They are created from JSONL case content and behave like a reusable file-backed experiment, but the UI only exposed archive. This ticket adds explicit permanent deletion for archived evaluation runs:

1. Active evaluation runs can be archived first.
2. Archived evaluation runs can be permanently deleted by users with `resources:delete`.
3. Permanent deletion removes the run, results, metrics, and the uploaded evaluation cases created for that run.
4. The frontend shows `Delete permanently` only for archived runs.

## Why Two Steps
Evaluation results are audit evidence. Immediate hard-delete would make it too easy to destroy quality and cost history by accident. Archive keeps the normal audit path safe; permanent delete exists for owner-controlled cleanup.

## Permission Rules
- Archive evaluation run: `resources:delete`.
- Permanently delete archived evaluation run: `resources:delete`.
- Move evaluation run between folders: `resource_folders:manage`.
- Read evaluations: `evaluations:read`.

## Frontend Rule For Future Work
Any page that can grow through uploaded files, imported datasets, created agents, or repeated experiment runs should use this pattern:

- folder panel for resource grouping;
- search box scoped to the selected folder;
- bounded visible list with a clear hidden-count note;
- move action if folders are supported;
- lifecycle action such as delete/archive based on backend permissions;
- no large flat list of file/resource names inside a form.

## Validation
Validated in this ticket:

- `cd backend && uv run pytest -s -q tests/test_evaluations.py tests/test_resource_folders.py` -> 16 passed, 1 warning.
- `cd backend && uv run ruff check app/api/v1/evaluations.py app/services/evaluation_runner.py tests/test_evaluations.py` -> passed.
- `cd frontend && npm run build` -> passed.
- `git diff --check` -> passed.

## Human Review Checklist
- Confirm the evaluation UI makes archive vs permanent delete clear.
- Confirm deleted evaluation runs no longer appear even when archived runs are shown.
- Confirm knowledge and dataset pages still expose folder, move, and delete actions.
- Confirm growing admin lists remain searchable and bounded.

## Interview Notes
This demonstrates a practical product tradeoff: preserve evaluation audit history by default, but provide owner-gated cleanup for local/team environments. It also shows a scalable UI pattern without overbuilding server-side pagination in the first local-first version.
