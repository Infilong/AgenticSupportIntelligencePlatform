# Knowledge File Browser Layout

## Goal
Make the Knowledge document library behave like a file browser: compact file rows, immediate selected-document visibility, and bounded per-row controls.

## Context
The previous card layout made every document occupy too much vertical space. Clicking a file did not make the editing/detail result obvious because the selected document area could sit below the long list.

## Changes
- Converted the Knowledge workbench to a file-browser layout with folders spanning the top, compact document list on the left, and selected document editor visible on the right.
- Made document rows compact: title/status, metadata, folder select, and delete action stay in one bounded row.
- Kept the editor sticky on desktop so selecting a document updates a visible panel without requiring discovery by scrolling.
- Preserved a single-column responsive layout for smaller screens.

## Validation Plan
- Run frontend typecheck and production build.
- Use Chrome visual QA with a seeded multilingual workspace to verify row height, selected editor visibility after click, and no controls outside row bounds.


## Validation Results
- npm --prefix frontend run typecheck passed.
- npm --prefix frontend run build passed.
- docker compose up -d --build frontend rebuilt and restarted the served app.
- Chrome visual QA at http://127.0.0.1:5174 seeded 8 English/Japanese/Chinese knowledge documents, selected a document, and verified:
  - document rows are compact at about 60px high;
  - selected row count is 1;
  - the editor/details panel is visible beside the document list on desktop;
  - row children stay inside their card bounds;
  - horizontal overflow is 0.
