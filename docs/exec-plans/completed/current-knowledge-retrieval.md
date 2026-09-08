# Retrieve current knowledge versions

## Goal
Keep obsolete policy text out of new retrieval/model context after document reindexing.
## Context
The multilingual regression returns versions 1 and 2 for an indexed document after updating it.
Evidence: `.artifacts/20260907-retrieval-versions/before.log`, three failing language cases.
## Requirements
Select only the latest version per document within the authorized workspace, before scoring.
Retain historical versions and trace references. Preserve language/document filters and denial paths.
## Non-goals
Embedding replacement, query scaling, indexing concurrency or historical trace redesign.
## Acceptance Criteria
EN/JA/ZH queries after reindex return only current content/citations; historical versions remain;
existing retrieval and knowledge management permission tests continue passing.
## Plan
RetrievalService owns a workspace-scoped latest-version subquery. No API, UI or schema changes.
Focused tests reproduce the stale response; run existing retrieval/knowledge regressions and lint.
## Verification
Prove the regression fails first; run corrected tests and verify the query on live PostgreSQL.
Inspect response versions and trace citations; check the diff and source-size gate.
## Risks
Latest means highest document version, consistent with the document inspector. Failed indexing
already marks the whole document failed; do not silently fall back to an older policy.
## Progress
2026-09-07: reproduced obsolete evidence in all three languages before implementation.
The repaired query passed 25 retrieval/knowledge tests and 24 agent tests. History assertions
confirm versions 1 and 2 remain stored; new searches return only version 2. Backend lint passes.
Live PostgreSQL API probes repeated upload/reindex/search in EN/JA/ZH with version-2 citations.
Evidence and reproducible live probe: `.artifacts/20260907-retrieval-versions/`.
## Decisions
Filter in SQL rather than dropping old chunks after ranking or deleting history.
## Findings
The old candidate query scoped workspace and language correctly but omitted current-version selection.
## Final Result
Completed for current-version filtering. No schema/UI changes and no historical record deletion.
Mock embedding quality, concurrent indexing and full multilingual demo acceptance remain open.
