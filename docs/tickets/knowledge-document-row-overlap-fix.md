# Knowledge Document Row Overlap Fix

## Goal
Fix the Knowledge page document list so expanded folder controls and delete actions stay inside their own document row.

## Context
The document list used compact expandable folder pickers inside each document card. That control was too large for a dense list and could visually overlap neighboring document rows when expanded or when global resource-row styles leaked in.

## Changes
- Removed the generic `.resource-main-button` class from Knowledge document headers so global resource-row rules cannot reshape this page-specific control.
- Scoped metadata styling to `.document-metadata` so nested badge spans keep their own sizing and tone.
- Added focused `knowledge-page.css` overrides for each `.document-card` so it has its own border, padding, and visible overflow.
- Made the document select button use a stable title/status grid without depending on generic resource-row classes.
- Renamed the document row action wrapper to `.document-card-actions` so shared `.resource-actions` rules cannot leak into this page.
- Replaced the per-document expandable folder picker with a bounded native folder select so list rows cannot expand over neighboring rows.
- Made document actions use a two-column grid that collapses on small screens.

## Validation Results
- `npm --prefix frontend run typecheck` passed.
- `npm --prefix frontend run build` passed.
- `docker compose up -d --build frontend` completed and restarted the local app.
- Browser smoke was attempted through gstack browse, but the daemon failed to start within 15 seconds.
- Browser smoke was attempted through Playwright, but WSL Chromium failed to launch because `libnspr4.so` is missing.

## Manual Review Checklist
- Open Knowledge with several documents.
- Expand multiple Move controls and verify each picker remains inside its document row.
- Verify Delete buttons do not cover titles, metadata, or neighboring rows.
