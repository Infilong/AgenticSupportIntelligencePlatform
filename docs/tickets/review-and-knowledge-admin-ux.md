# Human Review Context and Knowledge Admin UX

## Goal
Make two confusing professional-tool areas clearer and more operational: human review and knowledge document management.

## Context
The review page previously showed guardrail names and a proposed-answer field but did not include the customer message or graph-run route context. That made valid review states look broken. Knowledge documents already supported upload and reindex, but the UI did not expose a full management lifecycle for obsolete documents.

## Changes
- Human review API responses now include a `run` context object with input message, language, status, route decision, final answer, and timestamps.
- The review workbench now shows the customer request, run status, route, guardrail badges, proposed answer, reviewer decision, edited answer, and reviewer note in one queue card.
- Knowledge documents can now be deleted through a workspace-scoped `DELETE /knowledge-documents/{document_id}` API.
- The knowledge UI exposes a delete action for the selected document, alongside edit/reindex and new-document actions.

## Tests
- Review listing and resolve responses include the related graph-run context.
- Document deletion removes document versions, chunks, and embeddings.
- Document deletion is workspace-scoped and returns 404 across workspace boundaries.

## Verification
- `uv run ruff check .`
- `uv run pytest -s`
- `npm run test`
- `npm run build`

## Risks
- Delete is hard delete for the local portfolio version. A production SaaS version would likely use soft delete and audit retention.
- Review context is read from the graph run row only; deeper step-level context remains available through the existing trace viewer.

## Interview Notes
Explain the review page as a human-in-the-loop control surface: the model/guardrail system routes uncertain work to humans, the queue shows why it was routed, and the trace gives evidence before approval. Explain document delete as workspace-scoped admin control with cascading index cleanup.
