# Create Form Reset Audit

## Goal
After a successful create/import action, one-shot creation inputs should return to an empty ready state instead of retaining the submitted value and causing duplicate warnings or accidental repeat creation.

## Reset After Success
- Account workspace name clears after workspace creation.
- Resource folder name clears after creating dataset, knowledge, evaluation, or agent folders.
- Dataset import name and JSONL content clear after successful import.
- Agent create name clears after successful agent creation.
- Workspace member email already cleared before this ticket and remains unchanged.

## Intentionally Not Reset
- Knowledge document upload selects the created document and turns the form into an edit/reindex workflow.
- Prompt template creation keeps the template fields because repeated versions are intentional.
- Model config creation keeps model/pricing fields because users commonly create related routes and revisions.
- Workspace settings rename is an edit form, not a one-shot create form.

## Verification
- `npm --prefix frontend run build`
- Manually create a workspace, folder, dataset import, and agent; each one-shot create input should clear after success.
