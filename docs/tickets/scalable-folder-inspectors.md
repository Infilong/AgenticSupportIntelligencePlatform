# Scalable Folder Inspectors

## Goal
Keep folder-managed file resources usable as datasets and knowledge documents grow. The resource libraries are already organized by folders, but selected dataset examples and selected document chunks could still render as unbounded detail lists.

## Context
The platform now has owner-gated folder creation, rename, move, and delete controls for `dataset` and `knowledge_document` resources. The remaining frontend growth risk is inside selected-resource inspectors: large JSONL imports can contain many examples, and long source documents can produce many chunks.

## Requirements
- Preserve existing backend folder semantics for datasets and knowledge documents.
- Do not add fake folder types for unrelated resources.
- Add search to selected dataset examples and selected document chunks.
- Bound the visible inspector rows so the page does not grow without limit.
- Keep label editing and chunk inspection available from the same screens.
- Add browser coverage for the new inspector search controls.

## Non-goals
- No backend schema changes.
- No pagination API in this ticket.
- No nested folder UI. The backend supports `parent_folder_id`, but v1 stays flat until real usage needs hierarchy.

## Implementation Notes
- Added `MAX_VISIBLE_EXAMPLES` and `MAX_VISIBLE_CHUNKS` caps in the frontend.
- Added `exampleSearch` and `chunkSearch` state.
- Dataset examples now show a selected-dataset scope summary, search input, bounded result list, and a clear message when only the first matching examples are shown.
- Knowledge chunks now show selected-document scope, chunk search, bounded result list, and no-match/overflow guidance.
- Added shared CSS for inspector toolbars and bounded inspector lists.

## Audit Result
- Upload/import resources: datasets and knowledge documents both have folder assignment, move controls, and owner-gated deletion.
- Large selected-resource internals: examples and chunks are now searchable and bounded.
- Evaluation runs, prompts, models, and agents are not file-upload folder workflows; they use archive/grouping/status controls instead. Extending folder semantics to them should be a separate product decision.

## Verification
- `cd frontend && npm test -- --run` - typecheck passed.
- `cd frontend && npm run build` - production build passed.
- `docker compose up -d --build frontend` - rebuilt the browser target.
- `make frontend-e2e-docker` - 1 Playwright smoke test passed, including example/chunk search focus checks.

## Human Review Checklist
- Confirm dataset and knowledge pages still make the folder workflow obvious.
- Confirm search fields keep focus while typing.
- Confirm large detail lists no longer stretch the whole page.
- Confirm this does not pretend to solve backend pagination for very large datasets.
