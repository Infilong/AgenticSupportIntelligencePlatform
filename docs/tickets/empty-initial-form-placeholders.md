# Empty Initial Form Placeholders

## Goal
Remove real demo text from initial input and textarea values. Example content should appear as gray placeholder guidance, not as user-entered form data.

## Context
The UI previously opened with fields prefilled with demo emails, passwords, workspace names, dataset JSONL, knowledge document text, agent messages, evaluation cases, prompt templates, and model names. That made it unclear whether the user had already entered data and caused accidental submissions with sample content.

## Requirements
- Initial create/login/import/run text fields start empty.
- Example values move to placeholders.
- Required empty fields block submission through disabled buttons or submit-time validation.
- Existing edit flows still load saved resource content after the user selects a real resource.

## Non-goals
- Do not change backend behavior.
- Do not clear numeric configuration controls that represent real operational defaults.
- Do not remove scenario cards that intentionally fill the agent message when clicked.

## Implementation Notes
- Cleared initial React state for auth, workspace creation, dataset import, knowledge document creation, folder creation, agent creation/run message, evaluation runs, prompt source, and model name.
- Kept selects and numeric controls populated when they represent actual configuration defaults.
- Added placeholders to active page components and remaining AppShell-hosted forms.
- Added lightweight guards for empty folder, document, agent, evaluation, prompt, and model submissions.

## Verification
Run:

```bash
npm --prefix frontend run build
```

Manual QA:
- Open the login/register page and confirm auth fields are empty with gray placeholder text.
- Open Account and confirm workspace creation is empty until typed.
- Open Datasets/Documents/Agents/Evaluations/Prompts/Models and confirm sample content is placeholder-only.
- Select an existing resource and confirm edit forms still load the saved values.


## Follow-up: Placeholder Visual Clarity
The first fix moved demo values into placeholders, but long JSON/prompt placeholders still looked like real input content. This follow-up removes full sample payloads from placeholders, keeps only short guidance text, adds an explicit global placeholder style, and disables browser autocomplete on auth fields so refresh does not visually reinsert real credentials.
