# Sidebar Workspace List Moved To Account Page

## Goal
Keep the left sidebar focused on current context only, and use the right main Account page as the scrollable workspace browsing and management surface.

## Context
A bounded workspace finder was added to the sidebar, but the intended scroll area is the right main page. The sidebar should not contain the workspace list or workspace search field.

## Changes
- Removed the sidebar workspace search input.
- Removed the sidebar workspace scroll window and workspace list rows.
- Kept the current workspace summary and Manage action in the sidebar.
- Preserved the Account page as the place for workspace search, pagination, selection, creation, deletion, and permission review.

## Verification
- Run `npm run build` in `frontend/`.
- Manually verify the left panel shows only current workspace context and a Manage action.
- Manually verify workspace browsing happens from the Account page main content area.

## Human Review Checklist
- Left sidebar should not contain a workspace list.
- Left sidebar should not contain a workspace search input.
- Account page should remain the full workspace management surface.
- Selecting and managing workspaces should remain clear from the right main page.
