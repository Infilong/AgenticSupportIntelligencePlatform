# Knowledge Admin Workflow Redesign

## Goal
Make the Knowledge area feel like a professional retrieval-operations screen instead of a basic upload form. Users should be able to create, select, edit, reindex, delete, and inspect their workspace-owned knowledge documents without needing a manual.

## Product Rationale
Knowledge documents are the evidence source for the LangChain retrieval tool and LangGraph support workflow. The UI must show that relationship clearly: documents become indexed chunks, chunks become citations, and citations determine whether the agent can answer or routes to human review.

## Implemented Changes
- Replaced the old two-column upload/list layout with a Knowledge console.
- Added a hero/status area for document count, indexed count, selected chunks, and embedding count.
- Added a document library with selected state, status badges, updated timestamp, and error visibility.
- Added an editor panel for creating new documents or editing and reindexing an existing document.
- Added document delete access from the selected document editor.
- Added a retrieval inspector that shows version, language, chunk count, total tokens, embedding count, and chunk text.
- Added responsive CSS so the Knowledge workflow collapses cleanly on smaller screens.

## Verification
- `npm run test` -> passed (`tsc --noEmit`).
- `npm run build` -> passed (`tsc -b && vite build`).

## Human Review Notes
Review the Knowledge page visually at `/workspaces/{id}/documents` through the app navigation:
- Select an existing document and confirm the editor loads title, language, and source content.
- Type in the source textarea and confirm focus stays in the textarea.
- Save edits and confirm chunks refresh in the retrieval inspector.
- Confirm the document list selected state matches the editor and inspector.
- Confirm empty-state copy explains what to do next.

## Remaining Risks
- This improves structure and styling, but full visual QA should still be done in browser after the frontend container is rebuilt.
- The backend indexing behavior is unchanged in this ticket; if Chinese chunks still look poor, that needs a separate chunking-quality ticket.
