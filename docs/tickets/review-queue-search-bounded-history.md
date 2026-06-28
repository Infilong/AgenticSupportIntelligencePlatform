# Review Queue Search And Bounded History

## Goal
Make the Human review page usable for growing workspaces by turning pending and resolved reviews into searchable, bounded operational lists.

## Context
The review page already supports reviewer ownership, selected-case editing, trace inspection, and safer decisions. It still rendered all matching pending cases and all resolved history, which would become noisy as agent runs generate more review records.

## Requirements
- Add text search across pending queue and resolved history.
- Search must include reason, customer message, citations, reviewer identity, run id, decisions, stored answers, and review context.
- Limit rendered pending and resolved lists so large workspaces do not grow the page indefinitely.
- Keep the selected review detail tied to a visible queue item.
- Show clear overflow guidance telling the operator to narrow the list.

## Non-goals
- No backend pagination API in this ticket.
- No review-folder database model in this ticket.
- No change to review authorization or resolution behavior.

## Implementation
- Added `reviewSearch` state and a shared `reviewSearchFields` helper.
- Added `MAX_VISIBLE_REVIEWS` and bounded pending/resolved render lists.
- Added search input to the review queue controls.
- Added overflow notes for pending and resolved review lists.
- Kept queue filtering, sorting, claim/release, resolve, and trace inspection behavior unchanged.

## Verification
- Pending: run frontend build and diff checks after implementation.

## Risks And Follow-up
- This is still client-side filtering. A larger production deployment should add backend pagination and server-side search for human reviews.
- Review records are not folder-managed yet; if review history becomes a first-class archive workflow, add saved queues or assignment folders later.

## Interview Notes
Explain this as an operations scalability pass: even a local-first AI platform should avoid unbounded UI surfaces. The product now supports reviewer search and bounded evidence display while preserving traceability and decision safety.
