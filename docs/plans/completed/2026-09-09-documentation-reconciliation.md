# Documentation reconciliation — 2026-09-09

## Execution brief

User outcome: independently verify conflicting Markdown and align it with actual progress.
Scope: documentation only; no features, source refactors, service operations or resumed M2 work.
Owner: coordinating agent; bounded read-only independent reviewer `docs_review`.
Evidence: source at application checkpoint `2379915`, saved runtime/test checkpoint and M2 record.
Checks: independent initial/final review, documentation paths/instruction limits, preparation suite,
and diff inspection. Historical application results are not newly run evidence.

## Findings and dispositions

- Fixed README's obsolete UI and seed-demo claims; link current and planned topology separately.
- Fixed architecture's diagnostic-only worker claim and future-tense ingestion checks; distinguish
  application LangGraph plans from checkpointer compatibility tests. Added actual module/data map.
- Fixed STATUS's active/paused ambiguity and latest application checkpoint/CI reference.
- Fixed runbook contradictions about started services and ingestion; record frontend rebuild need.
- Removed the changing milestone snapshot from the backend guide; STATUS owns current progress.
- Recorded vector-plus-reranker versus lexical/fusion as an unresolved plan difference. The reviewer
  suggested a superseding decision; documentation repair alone does not authorize silently dropping
  the original requirement. Keep the difference visible until comparison or explicit scope resolution.
- Older conversation instructions reference files absent on the fresh branch. Root AGENTS.md is
  the current navigation map; do not recreate old product/context/rules files solely for those paths.

## Lesson applied

Adding new evidence without revising old summaries left contradictory current claims. Future
slices must inspect the affected entry points as well as append evidence. Owning docs hold facts;
guides link them. Link/size checks are useful but do not establish semantic freshness. This rule
is now in the documentation guide and development checkpoint protocol.

## Verification boundary

Review uses code and retained artifacts; no live application, browser or CI rerun is implied.
This documentation task does not extend the expired application implementation window.

Independent final review found no blocking accuracy issues; its optional directional wording
correction was applied. Documentation paths/instruction limits and all 19 preparation tests
passed at `.artifacts/m0/prep-20260909T000950103549Z`; later documentation-only edits require
the final preparation rerun before commit. `git diff --check` passed. No application source,
tests or schema changed. The coordinating agent verifies the final staged diff and branch push.
