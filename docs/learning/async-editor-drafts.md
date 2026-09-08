# Async responses and editor drafts

## What It Does
An editor draft distinguishes unsaved user input from the last saved API representation.
Request generations identify responses that no longer belong to the active selection.

## Why Companies Care
A successful HTTP response can still corrupt the user experience if it replaces newer input.
Fast local requests often hide this race until network latency or concurrent work increases.

## How This Project Uses It
`frontend/src/app/useAgentControls.ts` owns the agent-control draft and its dirty state.
List refreshes preserve a dirty draft for the same agent. Explicit selection or successful
save initializes controls, while superseded list requests are ignored. The shell continues
to own transport and rendering; this extraction reduces its size without a broad rewrite.

## Tradeoffs
Dirty controls retain their local values even if another client updates the saved agent.
This does not implement optimistic concurrency or conflict resolution on the backend.
Summary/workflow fetching remains separate and needs its own stale-response review.

## Failure Modes
Waiting for all requests before typing hides the race. Replacing typing with one atomic fill
can also hide focus bugs. Tests should deliberately release a response after an edit, and
prove that failed saves retain the draft. A request completing is not evidence it is current.

## Project Explanation
The delayed-response regression fails against the original shell because the cleared name
is restored from the server. Its assertion checks user-visible preservation of input,
rather than the hook's internal flags. Original failures and later runs stay in `.artifacts/`.
