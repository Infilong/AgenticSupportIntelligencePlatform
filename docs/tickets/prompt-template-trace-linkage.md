# Prompt Template Trace Linkage

## Goal
Make prompt versioning real in the support-agent trace by persisting default LangChain prompt templates and linking them to AI run ledger records.

## Audit Finding
The data model already had `PromptTemplate`, and trace UI showed prompt template/version fields, but classification and draft-response AI runs did not actually reference persisted prompt templates. This made prompt versioning look theoretical instead of operational.

## Changes Made
- Split LangChain prompt helper constants into reusable template source strings.
- Added `PromptTemplateService.get_or_create_default` for workspace-scoped default prompt templates.
- Persisted default prompt templates for:
  - `support_intent_classifier`
  - `support_response_drafter`
- Linked those templates to classification and draft-response `AIRun` records.
- Extended trace AI run response with `prompt_template_name` and `prompt_template_text`.
- Updated frontend trace AI run panel to show prompt template name/version and expandable prompt template source.
- Strengthened backend tests to assert prompt templates are created and attached to AI runs.

## Verification
- `make backend-lint`
- `make backend-test`
- `npm run test`
- `npm run build`
- `docker compose up -d --build api frontend`
- Live API smoke confirmed trace returns two prompt template names, both version `1`, and non-empty template text.

## Remaining Risks
- Prompt templates are created automatically but not editable from an admin settings page yet.
- Prompt versioning is fixed at v1 for now; future work should add explicit create-new-version behavior and active-template selection.
- Prompt templates are workspace-scoped, so the first agent run in a workspace creates the defaults lazily.

## Next Recommended Ticket
Add a developer/admin prompt settings page or API for listing prompt templates, creating a new version, selecting active prompts, and comparing evaluation results by prompt version.
