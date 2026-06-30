# Account Workspace Management Page

## Goal
Move workspace creation out of the sidebar into a dedicated account management page so the product workflow is clearer and closer to a GitHub-style profile/workspace entry point.

## Context
The sidebar previously mixed navigation, active workspace selection, permission summary, and a raw workspace-name input with a `Create` button. That made the app confusing because users could not tell whether the control created a workspace, changed settings, or created a task.

## Implemented Behavior
- Added an Account page that is available even before a workspace exists.
- The page shows current user identity, workspace counts, selected workspace role, permissions, pending reviews, and open task count.
- Workspace creation now happens from the Account page with clear explanatory copy.
- Users can switch active workspace from the Account page.
- The sidebar now links to `Account & workspaces` instead of exposing a raw create form.

## Non-goals
- No backend profile-edit endpoint was added.
- No fake manual task creation was added because there is no task-create API in this slice.
- No workspace deletion was added here; resource deletion remains handled on resource pages and workspace lifecycle requires separate policy review.

## Verification
- Run `npm --prefix frontend run build`.
- Open the app and verify `Account` is visible in navigation.
- With no workspace selected, verify Account can still render and create a workspace.
- Verify sidebar workspace selection still switches context.

## Human Review Notes
- Confirm the Account page language makes it obvious that a workspace is the isolated project boundary.
- Confirm the old sidebar input is gone.
- Confirm task/profile features are not presented as implemented if the backend does not support them.
