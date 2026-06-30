# Workspace Duplicate Name And Status Stability

## Goal
Prevent confusing duplicate workspace names for the same user and stop create-action status messages from making the UI jump.

## Context
The Account page allowed submitting a workspace name that already existed in the signed-in user's workspace list. The backend also accepted it, so the sidebar/account workspace switcher could show indistinguishable workspace rows. The global `Status` component only rendered when a notice/error existed, which inserted or removed vertical space after create actions.

## Implemented Behavior
- Backend rejects duplicate workspace names visible to the same user with `409 workspace_name_conflict`.
- Duplicate checks normalize leading/trailing spaces and case.
- Different users can still create workspaces with the same name because workspace names are not global identifiers.
- Workspace rename rejects names that would duplicate another workspace visible to the actor.
- Account page disables duplicate workspace submits and shows a stable inline validation note.
- Global status messages now render inside a reserved status slot to reduce page shaking after actions.

## Same-Issue Audit
- Workspace names were the direct bug and are fixed in backend and frontend.
- Resource folders reject delete conflicts but do not currently enforce duplicate folder names; this should be a separate folder semantics ticket because parent-folder behavior matters.
- Agent names can duplicate inside a workspace; this can be useful during experiments but may need a future warning if users report confusion.
- Model configs and prompt templates intentionally support repeated provider/model/purpose or versioned names, so those should not use a simple duplicate-name rule.

## Verification
- `uv run pytest -s tests/test_auth_workspace.py -q`
- `npm --prefix frontend run build`
- Run broader backend pytest before shipping because workspace permissions are cross-cutting.
